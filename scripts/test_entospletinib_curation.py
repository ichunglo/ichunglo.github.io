"""Guard the separate Gilead phase 2 and Kronos Bio phase 3 entospletinib decisions."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    programs = {row["program_id"]: row for row in read("programs.csv") if row["drug_id"] == "DRG-entospletinib"}
    assert set(programs) == {"PRG-entospletinib-hematology", "PRG-entospletinib-aml"}
    assert programs["PRG-entospletinib-hematology"]["inclusion_status"] == "needs_review"
    assert programs["PRG-entospletinib-aml"]["inclusion_status"] == "included"
    assert programs["PRG-entospletinib-aml"]["sponsor_id"] == "SPN-kronos-bio"
    assert {row["primary_target_id"] for row in programs.values()} == {"TGT-p43405-1"}

    sponsors = {row["sponsor_id"]: row for row in read("sponsors.csv")}
    assert sponsors["SPN-entospletinib"]["sponsor_name"] == "Gilead Sciences"
    assert sponsors["SPN-kronos-bio"]["sponsor_name"] == "Kronos Bio"

    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] in programs}
    assert set(trials) == {"NCT01799889", "NCT05020665"}
    assert trials["NCT01799889"]["program_id"] == "PRG-entospletinib-hematology"
    assert trials["NCT05020665"]["program_id"] == "PRG-entospletinib-aml"
    assert all(row["recruitment_status"] == "terminated" for row in trials.values())

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv") if row["program_id"] in programs}
    assert set(outcomes) == {"OUT-NCT01799889", "OUT-NCT05020665"}
    assert outcomes["OUT-NCT01799889"]["event_type"] == "strategic_discontinuation"
    assert outcomes["OUT-NCT05020665"]["event_type"] == "recruitment_failure"
    assert all(row["stated_or_inferred"] == "stated" for row in outcomes.values())
    assert all("efficacy" in row["description"] for row in outcomes.values())
    assert "does not state" in outcomes["OUT-NCT01799889"]["description"]
    assert "not a reported" in outcomes["OUT-NCT05020665"]["description"]
    print("Entospletinib curation: pass")


if __name__ == "__main__":
    main()
