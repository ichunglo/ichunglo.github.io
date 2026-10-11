"""Guard three separate balovaptan ASD trials and their source-backed results."""

from __future__ import annotations

import csv
from pathlib import Path


CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program = next(row for row in read("programs.csv") if row["program_id"] == "PRG-balovaptan-asd")
    assert program["inclusion_status"] == "included"
    assert program["lifecycle_status"] == "phase_3"
    assert program["primary_target_id"] == "TGT-p37288-1"

    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] == program["program_id"]}
    assert set(trials) == {"NCT01793441", "NCT02901431", "NCT03504917"}
    assert trials["NCT01793441"]["recruitment_status"] == "completed"
    assert trials["NCT02901431"]["phase"] == "phase_2"
    assert trials["NCT03504917"]["phase"] == "phase_3"
    assert "randomized phase 3 efficacy trial" in trials["NCT03504917"]["primary_endpoint_result"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv")}
    assert "OUT-PRG-balovaptan-asd" not in outcomes
    for nct, source in {
        "NCT01793441": "SRC-PUBMED-balovaptan-VANILLA",
        "NCT02901431": "SRC-JAMA-balovaptan-aV1ation",
        "NCT03504917": "SRC-LANCET-balovaptan-V1aduct",
    }.items():
        result = outcomes[f"OUT-{nct}"]
        assert result["event_type"] == "endpoint_failure"
        assert result["confidence"] == "high"
        assert result["source_id"] == source
    assert "favorable" in outcomes["OUT-NCT01793441"]["description"]
    assert "futility" in outcomes["OUT-NCT03504917"]["description"]
    print("Balovaptan curation: pass")


if __name__ == "__main__":
    main()
