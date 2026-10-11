"""Guard BRISK-PS attribution and the separate renal indication."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"
INTAKE = Path(__file__).resolve().parents[1] / "data" / "intake"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = {row["program_id"]: row for row in read("programs.csv")}
    hcc = programs["PRG-brivanib-hcc"]
    rcc = programs["PRG-brivanib-rcc"]
    assert hcc["drug_id"] == rcc["drug_id"] == "DRG-brivanib"
    assert hcc["inclusion_status"] == "needs_review"
    assert rcc["inclusion_status"] == "included"
    assert hcc["primary_target_id"] == rcc["primary_target_id"] == "TGT-unknown-brivanib"

    trials = {row["trial_id"]: row for row in read("trials.csv")}
    assert trials["NCT00825955"]["program_id"] == hcc["program_id"]
    assert trials["NCT00825955"]["recruitment_status"] == "completed"
    assert trials["NCT01108705"]["program_id"] == hcc["program_id"]
    assert trials["NCT01108705"]["recruitment_status"] == "terminated"
    assert trials["NCT01253668"]["program_id"] == rcc["program_id"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    assert outcomes["OUT-NCT00825955"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT00825955"]["source_id"] == "SRC-JCO-brivanib"
    assert outcomes["OUT-NCT01108705"]["event_type"] == "unknown"
    assert outcomes["OUT-PRG-brivanib-portfolio"]["event_type"] == "strategic_discontinuation"
    assert outcomes["OUT-PRG-brivanib-portfolio"]["primary_reason"] == "0"
    assert outcomes["OUT-PRG-brivanib-portfolio"]["source_id"] == "SRC-SEC-BMS-brivanib-2012"
    assert outcomes["OUT-NCT01253668"]["event_type"] == "strategic_discontinuation"
    assert outcomes["OUT-NCT01253668"]["source_id"] == "SRC-CTG-NCT01253668"
    with (INTAKE / "pilot-evidence-review-queue.csv").open(encoding="utf-8", newline="") as handle:
        queue = {row["trial_id"]: row for row in csv.DictReader(handle)}
    assert queue["NCT01108705"]["review_priority"] == "P1"
    assert "NCT00825955" not in queue
    print("Brivanib curation: pass")


if __name__ == "__main__":
    main()
