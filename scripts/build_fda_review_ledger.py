"""Build a primary-indication review ledger without promoting candidates to facts.

Only a source-backed decision in fda-review-decisions.csv can move a drug out
of pending. A no-name-match or label candidate never does so automatically.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from build_fda_review_queue import CURATED, QUEUE, ROOT, read_csv


DECISIONS = ROOT / "data/curated/fda-review-decisions.csv"
LEDGER = ROOT / "data/generated/fda-review-ledger.csv"
SUMMARY = ROOT / "data/generated/fda-review-ledger-summary.json"
ALLOWED = {"verified_primary_indication", "unresolved_after_review"}
FDA_HOSTS = {"www.fda.gov", "www.accessdata.fda.gov"}


def compile_ledger(
    queue: list[dict[str, str]],
    indications: list[dict[str, str]],
    decisions: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict]:
    by_drug = {row["drug_id"]: row for row in queue}
    indication_apps: dict[str, set[str]] = {}
    for row in indications:
        indication_apps.setdefault(row["drug_id"], set()).add(row["application_number"])
    by_decision: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for row in decisions:
        drug_id = row["drug_id"]
        if drug_id in by_decision:
            errors.append(f"duplicate FDA review decision: {drug_id}")
        by_decision[drug_id] = row
        if drug_id not in by_drug:
            errors.append(f"FDA review decision names unknown drug: {drug_id}")
        if row["review_status"] not in ALLOWED:
            errors.append(f"invalid FDA review status: {drug_id}")
        try:
            date.fromisoformat(row["reviewed_date"])
        except ValueError:
            errors.append(f"invalid FDA review date: {drug_id}")
        if len(row["review_note"].strip()) < 30 or len(row["supplement_review_note"].strip()) < 20:
            errors.append(f"FDA review notes too short: {drug_id}")
        urls = list(filter(None, row["source_urls"].split("|")))
        if len(urls) < 2 or any(
            urlparse(url).scheme != "https" or urlparse(url).hostname not in FDA_HOSTS
            for url in urls
        ):
            errors.append(f"FDA review must cite at least two FDA links: {drug_id}")
        if row["review_status"] == "verified_primary_indication":
            recorded = set(filter(None, row["applications_reviewed"].split("|")))
            if not indication_apps.get(drug_id):
                errors.append(f"primary-indication review lacks curated indication: {drug_id}")
            if not recorded or not indication_apps.get(drug_id, set()) <= recorded:
                errors.append(f"primary-indication review omits indication application: {drug_id}")
            if drug_id in by_drug and recorded != set(filter(None, by_drug[drug_id]["candidate_applications"].split("|"))):
                errors.append(f"primary-indication review has not reconciled every candidate application: {drug_id}")

    rows = []
    for drug in queue:
        decision = by_decision.get(drug["drug_id"], {})
        rows.append({
            "drug_id": drug["drug_id"],
            "generic_name": drug["generic_name"],
            "review_status": decision.get("review_status", "pending"),
            "reviewed_date": decision.get("reviewed_date", ""),
            "curated_indication_count": drug["curated_indication_count"],
            "candidate_match_basis": drug["candidate_match_basis"],
            "candidate_applications": drug["candidate_applications"],
            "applications_reviewed": decision.get("applications_reviewed", ""),
            "supplement_review_note": decision.get("supplement_review_note", ""),
            "source_urls": decision.get("source_urls", ""),
            "review_note": decision.get("review_note", ""),
        })
    counts = Counter(row["review_status"] for row in rows)
    summary = {
        "total_catalog_drugs": len(rows),
        "verified_primary_indication": counts["verified_primary_indication"],
        "unresolved_after_review": counts["unresolved_after_review"],
        "pending": counts["pending"],
        "primary_indication_audit_complete": len(rows) == 1766 and counts["pending"] == 0 and not errors,
        "warning": "A candidate row alone does not verify an FDA indication. Unresolved cases are not confirmed nonapprovals.",
        "errors": errors,
    }
    return rows, summary


def main() -> None:
    rows, summary = compile_ledger(read_csv(QUEUE), read_csv(CURATED), read_csv(DECISIONS))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
