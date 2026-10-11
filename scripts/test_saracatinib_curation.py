"""Keep the two prostate saracatinib protocols and outcomes distinct."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program_id = "PRG-saracatinib-prostate"
    program = next(row for row in read("programs.csv") if row["program_id"] == program_id)
    assert program["inclusion_status"] == "included"
    assert program["primary_target_id"] == "TGT-unknown-saracatinib"

    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] == program_id}
    assert set(trials) == {"NCT00513071", "NCT01267266"}
    assert trials["NCT00513071"]["recruitment_status"] == "completed"
    assert "zero qualifying PSA responses" in trials["NCT00513071"]["primary_endpoint_result"]
    assert trials["NCT01267266"]["recruitment_status"] == "terminated"
    assert "planned randomized" in trials["NCT01267266"]["primary_endpoint_result"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv") if row["program_id"] == program_id}
    assert set(outcomes) == {"OUT-NCT00513071", "OUT-NCT01267266"}
    assert outcomes["OUT-NCT00513071"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT00513071"]["source_id"] == "SRC-PMC-saracatinib-PSA"
    assert outcomes["OUT-NCT01267266"]["event_type"] == "lead_in_futility"
    assert outcomes["OUT-NCT01267266"]["source_id"] == "SRC-PMC-saracatinib-FYN"

    sources = {row["source_id"]: row for row in read("sources.csv")}
    assert sources["SRC-PMC-saracatinib-PSA"]["citation"] == "10.1097/CAD.0b013e328325a867"
    assert sources["SRC-PMC-saracatinib-FYN"]["citation"] == "10.1002/pros.23119"
    print("Saracatinib curation: pass")


if __name__ == "__main__":
    main()
