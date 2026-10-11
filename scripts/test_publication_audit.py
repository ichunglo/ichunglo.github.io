"""Regression checks for the publication-critical audit and its failure modes."""

from __future__ import annotations

from copy import deepcopy
from unittest.mock import patch

import validate_publication_audit as gate


def main() -> None:
    assert gate.audit()["status"] == "pass"
    tables = {
        name: gate.read(name)
        for name in (
            "programs.csv", "trials.csv", "outcomes.csv", "sources.csv",
            "targets.csv", "target-class-audit.csv", "publication-program-audit.csv",
        )
    }

    def check_failure(change, expected: str) -> None:
        altered = deepcopy(tables)
        change(altered)
        with patch.object(gate, "read", side_effect=lambda name: altered[name]):
            result = gate.audit()
        assert result["status"] == "fail"
        assert any(expected in message for message in result["errors"]), result["errors"]

    check_failure(
        lambda t: t["targets.csv"].__setitem__(0, {**t["targets.csv"][0], "protein_group": ""}),
        "target lacks explicit classification",
    )
    check_failure(
        lambda t: t["programs.csv"].__setitem__(
            next(i for i, r in enumerate(t["programs.csv"]) if r["program_id"] == "PRG-brivanib-hcc"),
            {**next(r for r in t["programs.csv"] if r["program_id"] == "PRG-brivanib-hcc"), "inclusion_status": "included"},
        ),
        "publication disposition disagrees",
    )
    check_failure(
        lambda t: t["outcomes.csv"].__setitem__(
            next(i for i, r in enumerate(t["outcomes.csv"]) if r["outcome_event_id"] == "OUT-PRG-lanabecestat-ad"),
            {**next(r for r in t["outcomes.csv"] if r["outcome_event_id"] == "OUT-PRG-lanabecestat-ad"), "confidence": "unknown"},
        ),
        "headline reason is unresolved",
    )
    check_failure(
        lambda t: t["trials.csv"].append({"trial_id": "NCT00627627", "program_id": "PRG-tanespimycin-solid-tumor"}),
        "retaspimycin trial",
    )
    check_failure(
        lambda t: t["outcomes.csv"].__setitem__(
            next(i for i, r in enumerate(t["outcomes.csv"]) if r["outcome_event_id"] == "OUT-NCT01108705"),
            {**next(r for r in t["outcomes.csv"] if r["outcome_event_id"] == "OUT-NCT01108705"), "event_type": "endpoint_failure"},
        ),
        "BRISK-APS stopping cause must remain explicitly unknown",
    )
    check_failure(
        lambda t: t["publication-program-audit.csv"].__setitem__(
            next(i for i, r in enumerate(t["publication-program-audit.csv"]) if r["program_id"] == "PRG-tideglusib-cdm"),
            {**next(r for r in t["publication-program-audit.csv"] if r["program_id"] == "PRG-tideglusib-cdm"), "disposition": "included"},
        ),
        "nine held programs must match",
    )
    print("Publication audit regression tests: pass")


if __name__ == "__main__":
    main()
