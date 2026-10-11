"""Guard the US efficacy trial versus global and safety-extension closures."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program_id = "PRG-tarenflurbil-ad"
    program = next(row for row in read("programs.csv") if row["program_id"] == program_id)
    assert program["inclusion_status"] == "included"
    assert program["primary_target_id"] == "TGT-unknown-tarenflurbil"
    assert program["target_status"] == "unclear"

    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] == program_id}
    assert set(trials) == {"NCT00105547", "NCT00322036", "NCT00380276"}
    assert trials["NCT00105547"]["recruitment_status"] == "completed"
    assert all(trials[trial_id]["recruitment_status"] == "terminated" for trial_id in ("NCT00322036", "NCT00380276"))
    assert "safety extension" in trials["NCT00380276"]["primary_endpoint_result"]

    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv") if row["program_id"] == program_id}
    assert set(outcomes) == {"OUT-NCT00105547", "OUT-NCT00322036", "OUT-NCT00380276"}
    assert outcomes["OUT-NCT00105547"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT00105547"]["primary_reason"] == "1"
    assert outcomes["OUT-NCT00105547"]["source_id"] == "SRC-JAMA-tarenflurbil-2009"
    for trial_id in ("NCT00322036", "NCT00380276"):
        event = outcomes[f"OUT-{trial_id}"]
        assert event["event_type"] == "cross_study_decision"
        assert event["primary_reason"] == "0"
        assert event["stated_or_inferred"] == "stated"

    sources = {row["source_id"]: row for row in read("sources.csv")}
    assert sources["SRC-JAMA-tarenflurbil-2009"]["citation"] == "10.1001/jama.2009.1866"
    assert sources["SRC-SEC-MYRIAD-Flurizan-2008"]["url"].startswith("https://www.sec.gov/")
    print("Tarenflurbil curation: pass")


if __name__ == "__main__":
    main()
