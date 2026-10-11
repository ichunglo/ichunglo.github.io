"""Build a compact quality report for target classification and relationships."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
GENERATED = ROOT / "data" / "generated"
INTAKE = ROOT / "data" / "intake"


def read(name):
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    targets = read("targets.csv")
    links = read("drug-targets.csv")
    drugs = read("drugs.csv")
    target_ids_with_links = {row["target_id"] for row in links}
    target_link_counts = Counter(row["target_id"] for row in links)
    drug_link_counts = Counter(row["drug_id"] for row in links)
    role_counts = Counter(row.get("target_role") or "unknown" for row in links)
    group_counts = Counter(row.get("protein_group") or "Unclassified" for row in targets)
    scope_counts = Counter(row.get("landscape_scope") or "unspecified" for row in targets)
    review_rows = [
        {
            "target_id": row["target_id"],
            "preferred_name": row["preferred_name"],
            "gene_symbol": row.get("gene_symbol", ""),
            "protein_group": row.get("protein_group", "") or "Unclassified",
            "landscape_scope": row.get("landscape_scope", ""),
            "target_status": row.get("target_status", ""),
            "linked_drug_count": str(target_link_counts.get(row["target_id"], 0)),
            "review_reason": "missing protein classification" if not row.get("protein_group") else "no linked drug-target relationship",
        }
        for row in targets
        if not row.get("protein_group") or row["target_id"] not in target_ids_with_links
    ]
    review_rows.sort(key=lambda row: (row["review_reason"], row["preferred_name"]))
    INTAKE.mkdir(parents=True, exist_ok=True)
    with (INTAKE / "target-coverage-review.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0].keys()) if review_rows else ["target_id"])
        writer.writeheader()
        writer.writerows(review_rows)
    report = {
        "target_total": len(targets),
        "drug_total": len(drugs),
        "drug_target_relationship_total": len(links),
        "target_class_counts": dict(sorted(group_counts.items())),
        "landscape_scope_counts": dict(sorted(scope_counts.items())),
        "relationship_role_counts": dict(sorted(role_counts.items())),
        "targets_with_no_drug_link": sum(1 for target in targets if target["target_id"] not in target_ids_with_links),
        "drugs_with_multiple_target_links": sum(1 for count in drug_link_counts.values() if count > 1),
        "review_queue_rows": len(review_rows),
        "review_queue_path": str(INTAKE / "target-coverage-review.csv"),
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "target-coverage-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
