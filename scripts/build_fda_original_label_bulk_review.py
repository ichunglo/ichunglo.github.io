"""Fetch and extract original FDA labels for clear, single-application candidates.

This bulk step intentionally produces a review file rather than curated facts.
Promotion still requires checking that the extracted label text and approval
letter identify the same product and support the selected first indication.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pypdf import PdfReader

from build_fda_review_queue import PRIMARY_QUEUE, ROOT, read_csv


DECISIONS = ROOT / "data/curated/fda-review-decisions.csv"
OUTPUT = ROOT / "data/generated/fda-original-label-bulk-review.csv"
SUMMARY = ROOT / "data/generated/fda-original-label-bulk-review-summary.json"
FDA_HOSTS = {"www.accessdata.fda.gov", "accessdata.fda.gov"}
FIELDS = [
    "drug_id", "generic_name", "application_number", "approval_date",
    "label_url", "approval_letter_url", "label_sha256", "letter_sha256",
    "label_indications_section", "approval_letter_indication_context",
    "label_product_identity_context", "bulk_review_status", "review_note",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in FDA_HOSTS


def fetch_document(url: str, cache_dir: Path) -> tuple[bytes, Path]:
    if not safe_url(url):
        raise ValueError(f"Non-FDA or non-HTTPS source refused: {url}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(urlparse(url).path).suffix.lower() or ".bin"
    path = cache_dir / (hashlib.sha256(url.encode()).hexdigest() + suffix)
    if path.exists() and path.stat().st_size:
        return path.read_bytes(), path
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": "ScientificBlogFDAIndicationAudit/1.0"})
            with urlopen(request, timeout=60) as response:
                content = response.read()
            if not content:
                raise ValueError("FDA document response was empty")
            path.write_bytes(content)
            return content, path
        except (HTTPError, TimeoutError, URLError, OSError, ValueError) as exc:
            last_error = exc
            if isinstance(exc, HTTPError) and exc.code not in {408, 429, 500, 502, 503, 504}:
                break
            if attempt < 4:
                time.sleep(min(2 ** attempt, 12))
    raise RuntimeError(f"Could not fetch FDA document {url}: {last_error}")


def text_from_document(content: bytes, path: Path) -> str:
    if path.suffix.lower() == ".pdf" or content.startswith(b"%PDF"):
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    parser = TextExtractor()
    parser.feed(content.decode("utf-8", errors="replace"))
    return "\n".join(parser.parts)


def extract_section(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    starts = list(re.finditer(r"\b(?:1\.?\s*)?INDICATIONS\s+AND\s+USAGE\b", text, re.I))
    if not starts:
        return ""
    start = starts[0].end()
    next_heading = re.search(
        r"\b(?:2\.?\s*)?DOSAGE\s+AND\s+ADMINISTRATION\b|"
        r"\b(?:2\.?\s*)?DOSAGE\s+FORMS\s+AND\s+STRENGTHS\b|"
        r"\b(?:3\.?\s*)?DOSAGE\s+FORMS\s+AND\s+STRENGTHS\b|"
        r"\b(?:2\.?\s*)?CONTRAINDICATIONS\b|"
        r"\b(?:3\.?\s*)?WARNINGS\s+AND\s+PRECAUTIONS\b|"
        r"\b(?:4\.?\s*)?WARNINGS\s+AND\s+PRECAUTIONS\b|"
        r"\b(?:4\.?\s*)?ADVERSE\s+REACTIONS\b|"
        r"\b(?:5\.?\s*)?ADVERSE\s+REACTIONS\b|"
        r"\b(?:6\.?\s*)?ADVERSE\s+REACTIONS\b|"
        r"\b(?:7\.?\s*)?DRUG\s+INTERACTIONS\b|"
        r"\b(?:8\.?\s*)?USE\s+IN\s+SPECIFIC\s+POPULATIONS\b|"
        r"\b(?:11\.?\s*)?DESCRIPTION\b|"
        r"\b(?:12\.?\s*)?CLINICAL\s+PHARMACOLOGY\b|"
        r"\b(?:14\.?\s*)?CLINICAL\s+STUDIES\b",
        text[start:], re.I,
    )
    end = start + next_heading.start() if next_heading else min(len(text), start + 12000)
    return text[start:end].strip(" :-\u2013\u2014")[:12000]


def letter_context(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    patterns = [
        r"\b(?:this|the)\s+(?:new\s+drug|biologics?\s+license)\s+application\s+provides\s+for\s+the\s+use\b",
        r"\b(?:NDA|BLA)\s+provides\s+for\s+the\s+use\b",
    ]
    candidates = [m for pattern in patterns for m in re.finditer(pattern, text, re.I)]
    if candidates:
        match = candidates[-1]
        end = re.search(r"\bAPPROVAL\s*(?:&|AND)\s*LABELING\b", text[match.start():], re.I)
        stop = match.start() + end.start() if end else min(len(text), match.start() + 2400)
        return text[match.start():stop].strip()[:2400]

    licensing = re.search(r"\bLICENSING\b", text, re.I)
    start = licensing.start() if licensing else 0
    matches = list(re.finditer(r"\b(?:is|are)\s+indicated\s+(?:for|to)\b", text[start:], re.I))
    if not matches:
        return ""
    match_start = start + matches[-1].start()
    return text[max(start, match_start - 260):match_start + 1700]


def identity_context(text: str, ingredient: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    name = re.escape(ingredient.strip())
    match = re.search(name, text, re.I) if name else None
    if not match:
        return ""
    return text[max(0, match.start() - 220):match.end() + 420]


def candidates() -> list[dict[str, str]]:
    decisions = {r["drug_id"]: r["review_status"] for r in read_csv(DECISIONS)}
    result = []
    for row in read_csv(PRIMARY_QUEUE):
        app_nums = row["candidate_first_approved_applications"].split("|")
        apps = row["candidate_applications"].split("|")
        labels = row["candidate_first_approval_label_urls"].split("|") if row["candidate_first_approval_label_urls"] else []
        letters = row["candidate_first_approval_letter_urls"].split("|") if row["candidate_first_approval_letter_urls"] else []
        if (
            decisions.get(row["drug_id"], "pending") == "pending"
            and row["candidate_match_basis"] == "exact_active_ingredient"
            and len(apps) == 1 and len(app_nums) == 1
            and apps[0].endswith(app_nums[0])
            and len(labels) == 1 and len(letters) == 1
            and safe_url(labels[0]) and safe_url(letters[0])
        ):
            result.append({**row, "label_url": labels[0], "letter_url": letters[0], "application_number": apps[0]})
    return result


def process(row: dict[str, str], cache_dir: Path) -> dict[str, str]:
    base = {
        "drug_id": row["drug_id"], "generic_name": row["generic_name"],
        "application_number": row["application_number"],
        "approval_date": row["candidate_first_approval_date"],
        "label_url": row["label_url"], "approval_letter_url": row["letter_url"],
        "label_sha256": "", "letter_sha256": "", "label_indications_section": "",
        "approval_letter_indication_context": "", "label_product_identity_context": "",
        "bulk_review_status": "fetch_or_extract_error", "review_note": "",
    }
    try:
        label_bytes, label_path = fetch_document(row["label_url"], cache_dir)
        letter_bytes, letter_path = fetch_document(row["letter_url"], cache_dir)
        label_text = text_from_document(label_bytes, label_path)
        letter_text = text_from_document(letter_bytes, letter_path)
        section = extract_section(label_text)
        context = letter_context(letter_text)
        identity = identity_context(label_text, row["generic_name"])
        base.update({
            "label_sha256": hashlib.sha256(label_bytes).hexdigest(),
            "letter_sha256": hashlib.sha256(letter_bytes).hexdigest(),
            "label_indications_section": section,
            "approval_letter_indication_context": context,
            "label_product_identity_context": identity,
        })
        if not section:
            base["bulk_review_status"] = "manual_label_section_review"
            base["review_note"] = "Could not extract a conventional INDICATIONS AND USAGE heading; inspect linked original FDA label."
        elif not context:
            base["bulk_review_status"] = "manual_approval_letter_review"
            base["review_note"] = "The approval letter did not yield an indication context automatically; inspect the linked FDA letter."
        else:
            base["bulk_review_status"] = "extracted_needs_identity_and_primary_use_check"
            base["review_note"] = "Exact ingredient and unique earliest application candidate; compare extracted indication to the FDA letter and confirm first-use selection before curation."
    except Exception as exc:  # keep the batch moving and expose failures for follow-up
        base["review_note"] = f"{type(exc).__name__}: {exc}"
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "tmp/fda-original-approval-docs")
    parser.add_argument("--retrieval-date", default=date.today().isoformat())
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--refresh-decisions", action="store_true",
        help="Sync an existing bulk source-extraction report with curated review decisions without re-fetching documents.",
    )
    args = parser.parse_args()
    date.fromisoformat(args.retrieval_date)
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    if args.refresh_decisions:
        if not OUTPUT.exists():
            parser.error(f"Bulk review file does not exist: {OUTPUT}")
        rows = read_csv(OUTPUT)
        decisions = {
            row["drug_id"]: row for row in read_csv(DECISIONS)
            if row["review_status"] == "verified_primary_indication"
        }
        synced = 0
        for row in rows:
            decision = decisions.get(row["drug_id"])
            if decision:
                row["bulk_review_status"] = "verified_primary_indication"
                row["review_note"] = (
                    "Original documents retained; curated primary-indication decision "
                    f"verified on {decision['reviewed_date']}. See canonical curated indication and decision rows."
                )
                synced += 1
        with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["bulk_review_status"]] = counts.get(row["bulk_review_status"], 0) + 1
        summary = {
            "retrieval_date": args.retrieval_date,
            "source_queue_snapshot_date": read_csv(PRIMARY_QUEUE)[0]["source_snapshot_date"],
            "source_queue_url": "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files",
            "catalog_drugs_in_bulk_batch": len(rows),
            "status_counts": counts,
            "curated_decisions_synced": synced,
            "this_command_created_or_promoted_no_curation_decisions": True,
            "warning": "Decision sync mirrors the canonical curated review ledger; it does not independently verify or promote indications.",
        }
        SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return
    items = candidates()
    results: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process, row, args.cache_dir): row for row in items}
        for index, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            if index % 20 == 0 or index == len(futures):
                print(f"Fetched and extracted original FDA documents for {index}/{len(futures)} drug candidates", flush=True)
    results.sort(key=lambda row: (row["generic_name"].casefold(), row["drug_id"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    counts: dict[str, int] = {}
    for row in results:
        counts[row["bulk_review_status"]] = counts.get(row["bulk_review_status"], 0) + 1
    summary = {
        "retrieval_date": args.retrieval_date,
        "source_queue_snapshot_date": read_csv(PRIMARY_QUEUE)[0]["source_snapshot_date"],
        "source_queue_url": "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files",
        "catalog_drugs_in_bulk_batch": len(results),
        "status_counts": counts,
        "verified_or_promoted_by_this_script": 0,
        "warning": "This is extracted source material, not verified curation. Promotion requires comparing original label and approval letter, confirming product identity, and selecting the earliest-use indication.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
