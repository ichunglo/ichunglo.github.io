"""Guard trial-specific LIGHT outcome and unresolved multikinase attribution."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program = next(row for row in read("programs.csv") if row["program_id"] == "PRG-linifanib-hcc")
    assert program["inclusion_status"] == "included"
    assert program["target_status"] == "unclear"
    assert program["primary_target_id"] == "TGT-unknown-linifanib"

    trial = next(row for row in read("trials.csv") if row["trial_id"] == "NCT01009593")
    assert trial["program_id"] == program["program_id"]
    assert trial["recruitment_status"] == "terminated"

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    assert "OUT-PRG-linifanib-hcc" not in outcomes
    result = outcomes["OUT-NCT01009593"]
    assert result["event_type"] == "endpoint_failure"
    assert result["primary_reason"] == "1"
    assert result["source_id"] == "SRC-JCO-linifanib-HCC"
    assert "not an inferred stopping cause" in result["description"]

    links = [row for row in read("drug-targets.csv") if row["drug_id"] == "DRG-linifanib"]
    assert {row["target_id"] for row in links if row["target_role"] == "primary"} == {
        "TGT-unknown-linifanib"
    }
    print("Linifanib curation: pass")


if __name__ == "__main__":
    main()
