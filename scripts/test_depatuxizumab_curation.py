"""Guard INTELLANCE-1 versus UNITE trial objectives and outcome attribution."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program_id = "PRG-depatuxizumab-gbm"
    program = next(row for row in read("programs.csv") if row["program_id"] == program_id)
    assert program["inclusion_status"] == "included"
    assert program["primary_target_id"] == "TGT-p00533-1"

    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] == program_id}
    assert set(trials) == {"NCT02573324", "NCT03419403"}
    assert trials["NCT02573324"]["recruitment_status"] == "completed"
    assert "overall-survival benefit" in trials["NCT02573324"]["primary_endpoint_result"]
    assert trials["NCT03419403"]["recruitment_status"] == "terminated"
    assert "ocular-side-effect prophylaxis" in trials["NCT03419403"]["primary_endpoint_result"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv") if row["program_id"] == program_id}
    assert set(outcomes) == {"OUT-NCT02573324", "OUT-NCT03419403"}
    assert outcomes["OUT-NCT02573324"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT02573324"]["primary_reason"] == "1"
    assert outcomes["OUT-NCT02573324"]["source_id"] == "SRC-OXFORD-depatuxizumab"
    assert outcomes["OUT-NCT03419403"]["event_type"] == "cross_study_decision"
    assert outcomes["OUT-NCT03419403"]["primary_reason"] == "0"
    assert outcomes["OUT-NCT03419403"]["source_id"] == "SRC-PUBMED-depatuxizumab-UNITE"

    sources = {row["source_id"]: row for row in read("sources.csv")}
    assert sources["SRC-OXFORD-depatuxizumab"]["citation"] == "10.1093/neuonc/noac173"
    print("Depatuxizumab curation: pass")


if __name__ == "__main__":
    main()
