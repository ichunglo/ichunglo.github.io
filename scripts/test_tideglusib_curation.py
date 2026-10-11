"""Guard unresolved single-primary attribution and supported tideglusib kinase links."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = [row for row in read("programs.csv") if row["drug_id"] == "DRG-tideglusib"]
    assert {row["program_id"] for row in programs} == {"PRG-tideglusib-ad", "PRG-tideglusib-cdm"}
    assert all(row["primary_target_id"] == "TGT-unknown-tideglusib" for row in programs)
    assert all(row["target_status"] == "unclear" for row in programs)

    targets = {row["target_id"]: row for row in read("targets.csv")}
    assert targets["TGT-p49840-1"]["gene_symbol"] == "GSK3A"
    assert targets["TGT-p49841-1"]["gene_symbol"] == "GSK3B"
    assert targets["TGT-unknown-tideglusib"]["landscape_scope"] == "unresolved"

    links = [row for row in read("drug-targets.csv") if row["drug_id"] == "DRG-tideglusib"]
    assert {(row["target_id"], row["target_role"], row["moa_status"]) for row in links} == {
        ("TGT-unknown-tideglusib", "primary", "unclear"),
        ("TGT-p49840-1", "secondary", "confirmed"),
        ("TGT-p49841-1", "secondary", "confirmed"),
    }
    assert all(row["source_id"].startswith("SRC-PUBMED-tideglusib-") for row in links)

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    pilot = outcomes["OUT-NCT00948259"]
    assert pilot["event_type"] == "unknown"
    assert pilot["primary_reason"] == "0"
    assert pilot["confidence"] == "high"
    assert pilot["source_id"] == "SRC-PUBMED-tideglusib-pilot"
    assert outcomes["OUT-NCT01350362"]["event_type"] == "endpoint_failure"
    queue_path = ROOT / "data" / "intake" / "pilot-evidence-review-queue.csv"
    with queue_path.open(encoding="utf-8", newline="") as handle:
        queue_ids = {row["trial_id"] for row in csv.DictReader(handle)}
    assert "NCT00948259" not in queue_ids
    print("Tideglusib curation: pass")


if __name__ == "__main__":
    main()
