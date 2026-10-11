"""Select 40 registry candidates for manual target/outcome review."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "intake" / "clinical-candidates.csv"
OUTPUT = ROOT / "data" / "intake" / "pilot-review-queue.csv"

TARGET_MAP = {
    "AMG 386": "ANGPT2 / angiopoietin pathway",
    "balovaptan": "AVPR1A",
    "bapineuzumab": "APP / amyloid-beta",
    "brivanib": "VEGFR2 / FGFR",
    "crenezumab": "APP / amyloid-beta",
    "darapladib": "PLA2G7",
    "depatuxizumab mafodotin": "EGFR",
    "entospletinib": "SYK",
    "glembatumumab": "GPNMB",
    "idalopirdine": "HTR6",
    "linifanib": "VEGFR2 / FGFR",
    "motesanib": "VEGFR2 / KIT",
    "onartuzumab": "MET",
    "pevonedistat": "NAE1",
    "rigosertib": "PLK1 / unclear polypharmacology",
    "rolofylline": "ADORA1",
    "rovalpituzumab tesirine": "DLL3",
    "saracatinib": "SRC",
    "siltuximab": "IL6",
    "solanezumab": "APP / amyloid-beta",
    "tarenflurbil": "gamma-secretase modulation / unclear",
    "tideglusib": "GSK3B",
    "tivantinib": "MET / unclear mechanism",
    "varespladib": "PLA2G1B",
}


def main() -> None:
    with INPUT.open(encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    groups: dict[str, list[dict[str, str]]] = {}
    for row in candidates:
        groups.setdefault(row["search_term"], []).append(row)

    selected: list[dict[str, str]] = []
    for search_term in sorted(groups):
        for row in groups[search_term][:2]:
            selected.append({
                "review_id": f"REVIEW-{row['nct_id']}",
                "candidate_id": row["candidate_id"],
                "search_term": search_term,
                "nct_id": row["nct_id"],
                "title": row["title"],
                "status": row["status"],
                "phases": row["phases"],
                "sponsor": row["sponsor"],
                "conditions": row["conditions"],
                "registry_url": row["registry_url"],
                "provisional_target": TARGET_MAP.get(search_term, ""),
                "target_review_status": "needs_review",
                "outcome_review_status": "needs_review",
                "failure_reason": "",
                "evidence_grade": "registry_only",
                "curation_notes": "Verify program identity, target role, and outcome reason before promotion.",
            })
    selected = selected[:40]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0].keys()))
        writer.writeheader()
        writer.writerows(selected)
    print(f"selected={len(selected)}")


if __name__ == "__main__":
    main()
