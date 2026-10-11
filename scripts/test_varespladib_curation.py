"""Guard cardiovascular biomarker outcomes and separate sickle-cell attribution."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = {row["program_id"]: row for row in read("programs.csv")}
    cardiovascular = programs["PRG-varespladib-cardiovascular"]
    sickle = programs["PRG-varespladib-sickle-cell"]
    assert cardiovascular["drug_id"] == sickle["drug_id"] == "DRG-varespladib"
    assert cardiovascular["inclusion_status"] == sickle["inclusion_status"] == "included"
    assert cardiovascular["primary_target_id"] == sickle["primary_target_id"] == "TGT-unknown-varespladib"

    trials = {row["trial_id"]: row for row in read("trials.csv")}
    for trial_id in ("NCT00455546", "NCT00743925", "NCT01130246"):
        assert trials[trial_id]["program_id"] == cardiovascular["program_id"]
    assert trials["NCT01522196"]["program_id"] == sickle["program_id"]
    assert trials["NCT01522196"]["recruitment_status"] == "terminated"

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    for trial_id, source_id in (
        ("NCT00455546", "SRC-LANCET-varespladib-PLASMA"),
        ("NCT00743925", "SRC-JACC-varespladib-FRANCIS"),
    ):
        event = outcomes[f"OUT-{trial_id}"]
        assert event["event_type"] == "biomarker_endpoint_met"
        assert event["primary_reason"] == "0"
        assert event["source_id"] == source_id
    assert outcomes["OUT-NCT01130246"]["event_type"] == "risk_benefit_discontinuation"
    assert outcomes["OUT-NCT01522196"]["event_type"] == "strategic_discontinuation"
    assert outcomes["OUT-NCT01522196"]["program_id"] == sickle["program_id"]
    print("Varespladib curation: pass")


if __name__ == "__main__":
    main()
