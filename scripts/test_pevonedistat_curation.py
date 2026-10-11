"""Guard indication-specific pevonedistat attribution and stopping reasons."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = {row["program_id"]: row for row in read("programs.csv")}
    lung = programs["PRG-pevonedistat-nsclc"]
    meso = programs["PRG-pevonedistat-mesothelioma"]
    assert lung["drug_id"] == meso["drug_id"] == "DRG-pevonedistat"
    assert lung["inclusion_status"] == "included"
    assert meso["inclusion_status"] == "needs_review"
    assert lung["primary_target_id"] == meso["primary_target_id"] == "TGT-unknown-pevonedistat"

    trials = {row["trial_id"]: row for row in read("trials.csv")}
    assert trials["NCT03228186"]["program_id"] == lung["program_id"]
    assert trials["NCT03319537"]["program_id"] == meso["program_id"]
    assert trials["NCT03228186"]["recruitment_status"] == "terminated"
    assert "22% objective response" in trials["NCT03228186"]["primary_endpoint_result"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    assert outcomes["OUT-PRG-pevonedistat-nsclc"]["event_type"] == "strategic_discontinuation"
    assert outcomes["OUT-NCT03319537"]["program_id"] == meso["program_id"]
    assert outcomes["OUT-NCT03319537"]["event_type"] == "unknown"
    assert not any(
        row["program_id"] in {lung["program_id"], meso["program_id"]}
        and row["event_type"] == "endpoint_failure"
        for row in outcomes.values()
    )

    sources = {row["source_id"]: row for row in read("sources.csv")}
    assert sources["SRC-PUBMED-pevonedistat-NSCLC"]["citation"] == "PMID 37977950"
    print("Pevonedistat curation: pass")


if __name__ == "__main__":
    main()
