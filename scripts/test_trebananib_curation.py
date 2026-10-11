"""Guard the trial identities and mixed primary outcomes in the trebananib pilot."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def read(name: str) -> list[dict[str, str]]:
    with (CURATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    program_id = "PRG-trebananib-ovarian"
    program = next(row for row in read("programs.csv") if row["program_id"] == program_id)
    assert program["primary_target_id"] == "TGT-unknown-trebananib"
    assert program["target_status"] == "unclear"
    targets = {row["target_id"]: row for row in read("targets.csv")}
    assert targets["TGT-q15389-clinical"]["gene_symbol"] == "ANGPT1"
    assert targets["TGT-o15123-1"]["gene_symbol"] == "ANGPT2"
    links = [row for row in read("drug-targets.csv") if row["drug_id"] == "DRG-trebananib"]
    assert {(row["target_id"], row["target_role"], row["moa_status"]) for row in links} == {
        ("TGT-unknown-trebananib", "primary", "unclear"),
        ("TGT-q15389-clinical", "secondary", "confirmed"),
        ("TGT-o15123-1", "secondary", "confirmed"),
    }
    assert all(row["source_id"] == "SRC-PUBMED-trebananib-TRINOVA3" for row in links)
    trials = {row["trial_id"]: row for row in read("trials.csv") if row["program_id"] == program_id}
    assert set(trials) == {"NCT01204749", "NCT01281254", "NCT01493505"}
    assert all(row["phase"] == "phase_3" for row in trials.values())
    assert trials["NCT01204749"]["recruitment_status"] == "completed"
    assert "met its primary PFS" in trials["NCT01204749"]["primary_endpoint_result"]
    outcomes = {row["outcome_event_id"]: row for row in read("outcomes.csv") if row["program_id"] == program_id}
    assert "OUT-PRG-trebananib-ovarian" not in outcomes
    assert outcomes["OUT-NCT01204749"]["event_type"] == "unknown"
    assert outcomes["OUT-NCT01204749"]["primary_reason"] == "0"
    assert outcomes["OUT-NCT01281254"]["event_type"] == "endpoint_failure"
    assert outcomes["OUT-NCT01493505"]["event_type"] == "endpoint_failure"
    assert all(row["source_id"].startswith("SRC-PUBMED-trebananib-") for row in outcomes.values())
    print("Trebananib curation: pass")


if __name__ == "__main__":
    main()
