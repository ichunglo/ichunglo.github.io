"""Guard separation of motesanib extension, MONET1 efficacy, and squamous safety."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = {row["program_id"]: row for row in read("programs.csv")}
    extension = programs["PRG-motesanib-cancer"]
    lung = programs["PRG-motesanib-nsclc"]
    assert extension["drug_id"] == lung["drug_id"] == "DRG-motesanib"
    assert extension["inclusion_status"] == "needs_review"
    assert lung["inclusion_status"] == "included"
    assert lung["lifecycle_status"] == "phase_3"
    assert extension["primary_target_id"] == lung["primary_target_id"] == "TGT-unknown-motesanib"

    trials = {row["trial_id"]: row for row in read("trials.csv")}
    assert trials["NCT00360867"]["program_id"] == extension["program_id"]
    assert trials["NCT00460317"]["program_id"] == lung["program_id"]
    assert trials["NCT00360867"]["recruitment_status"] == "terminated"
    assert trials["NCT00460317"]["phase"] == "phase_3"

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    assert outcomes["OUT-NCT00360867"]["event_type"] == "unknown"
    assert outcomes["OUT-NCT00360867"]["primary_reason"] == "0"
    assert outcomes["OUT-NCT00460317"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT00460317"]["source_id"] == "SRC-JCO-motesanib-MONET1"
    assert outcomes["OUT-NCT00460317-squamous"]["event_type"] == "safety_failure"
    assert outcomes["OUT-NCT00460317-squamous"]["primary_reason"] == "0"
    assert outcomes["OUT-NCT00460317-squamous"]["source_id"] == "SRC-JTO-motesanib-MONET1-squamous"
    assert "OUT-PRG-motesanib-cancer" not in outcomes
    print("Motesanib curation: pass")


if __name__ == "__main__":
    main()
