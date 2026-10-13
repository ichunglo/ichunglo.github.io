"""Fetch current FDA label *candidates* for matched applications.

This is a triage aid, not a verified indication table. openFDA labeling is a
current-label feed; it does not supply the first approval date of each use.
Product association and historical supplements still require FDA review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_fda_review_queue import QUEUE, ROOT, read_csv


API = "https://api.fda.gov/drug/label.json"
OUTPUT = ROOT / "data/generated/fda-label-candidates.csv"
SUMMARY = ROOT / "data/generated/fda-label-candidates-summary.json"
FIELDS = [
    "drug_id", "generic_name", "candidate_match_basis", "application_number",
    "label_status", "label_record_count", "effective_time", "spl_set_id",
    "label_generic_names", "label_brand_names", "indications_and_usage",
    "source_api_url", "review_status",
]


def application_candidates(queue: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_app: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in queue:
        for app in filter(None, row["candidate_applications"].split("|")):
            if app.startswith(("NDA", "BLA")):
                by_app[app].append(row)
    return dict(by_app)


def batch_url(applications: list[str]) -> str:
    term = "openfda.application_number:(" + " OR ".join(applications) + ")"
    return API + "?" + urlencode({"search": term, "limit": 1000})


def fetch(url: str, attempts: int = 5) -> dict:
    request = Request(url, headers={"User-Agent": "ScientificBlogFDAIndicationAudit/1.0"})
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code == 404:
                return {"meta": {"results": {"total": 0}}, "results": []}
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except (TimeoutError, URLError):
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable FDA API retry state")


def load_batch(apps: list[str], cache_dir: Path) -> tuple[dict, str]:
    url = batch_url(apps)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    path = cache_dir / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), url
    result = fetch(url)
    if result.get("meta", {}).get("results", {}).get("total", 0) > 1000:
        raise RuntimeError("FDA label query exceeded the 1000-record limit")
    path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result, url


def select_label(records: list[dict]) -> dict | None:
    eligible = [r for r in records if r.get("indications_and_usage")]
    return max(eligible, key=lambda r: r.get("effective_time", "")) if eligible else None


def make_rows(queue: list[dict[str, str]], batches: list[tuple[list[str], dict, str]]) -> list[dict[str, str]]:
    by_app: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for apps, payload, url in batches:
        selected = set(apps)
        for item in payload.get("results", []):
            for app in item.get("openfda", {}).get("application_number", []):
                if app in selected:
                    by_app[app].append((item, url))
    rows = []
    for drug in queue:
        for app in filter(None, drug["candidate_applications"].split("|")):
            matches = by_app.get(app, [])
            chosen = select_label([record for record, _ in matches])
            provenance_url = next((url for record, url in matches if record is chosen), batch_url([app]))
            fda = chosen.get("openfda", {}) if chosen else {}
            rows.append({
                "drug_id": drug["drug_id"],
                "generic_name": drug["generic_name"],
                "candidate_match_basis": drug["candidate_match_basis"],
                "application_number": app,
                "label_status": "current_label_candidate" if chosen else "no_indication_text_found",
                "label_record_count": str(len(matches)),
                "effective_time": chosen.get("effective_time", "") if chosen else "",
                "spl_set_id": chosen.get("set_id", "") if chosen else "",
                "label_generic_names": "|".join(fda.get("generic_name", [])),
                "label_brand_names": "|".join(fda.get("brand_name", [])),
                "indications_and_usage": "\n".join(chosen.get("indications_and_usage", [])) if chosen else "",
                "source_api_url": provenance_url,
                "review_status": "candidate_not_indication_verified",
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "tmp/fda-label-api")
    parser.add_argument("--retrieval-date", default=date.today().isoformat())
    args = parser.parse_args()
    date.fromisoformat(args.retrieval_date)
    queue = read_csv(QUEUE)
    by_app = application_candidates(queue)
    apps = sorted(by_app)
    batches = []
    for offset in range(0, len(apps), 20):
        group = apps[offset:offset + 20]
        payload, url = load_batch(group, args.cache_dir)
        batches.append((group, payload, url))
        print(f"FDA label batch {offset // 20 + 1}/{(len(apps) + 19) // 20}: {len(group)} applications", flush=True)
    rows = make_rows(queue, batches)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "source_api": API,
        "retrieval_date": args.retrieval_date,
        "source_queue_snapshot_date": queue[0]["source_snapshot_date"],
        "warning": "Current FDA label candidates do not verify drug association, all indications, or indication-specific approval dates.",
        "catalog_drugs": len(queue),
        "unique_candidate_applications": len(apps),
        "drug_application_candidate_rows": len(rows),
        "rows_with_indication_text": sum(r["label_status"] == "current_label_candidate" for r in rows),
        "drugs_with_indication_text_candidate": len({r["drug_id"] for r in rows if r["label_status"] == "current_label_candidate"}),
        "drugs_without_application_candidate": sum(not r["candidate_applications"] for r in queue),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
