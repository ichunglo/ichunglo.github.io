"""Fail a release when audited uncertainty leaks into headline findings."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
GENERATED = ROOT / "data" / "generated"


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit() -> dict[str, object]:
    programs = {row["program_id"]: row for row in read("programs.csv")}
    trials = read("trials.csv")
    outcomes = read("outcomes.csv")
    sources = {row["source_id"]: row for row in read("sources.csv")}
    targets = {row["target_id"]: row for row in read("targets.csv")}
    target_audit = read("target-class-audit.csv")
    program_audit = read("publication-program-audit.csv")
    errors: list[str] = []

    if len(target_audit) != 139 or len({r["target_id"] for r in target_audit}) != len(target_audit):
        errors.append("target-class audit must cover 139 unique inherited unclassified records")
    for row in target_audit:
        target = targets.get(row["target_id"])
        if target is None or target["protein_group"] != row["audited_group"]:
            errors.append(f"target-class audit disagrees with target: {row['target_id']}")
        if not row["audit_basis"] or (row["audited_group"] == "Unresolved" and not row["audit_basis"]):
            errors.append(f"target-class audit lacks rationale: {row['target_id']}")
    for row in targets.values():
        if not row["protein_group"]:
            errors.append(f"target lacks explicit classification: {row['target_id']}")

    if len(program_audit) != 11 or len({r["program_id"] for r in program_audit}) != len(program_audit):
        errors.append("publication-program audit must cover 11 unique original provisional programs")
    audited = {row["program_id"]: row for row in program_audit}
    for row in program_audit:
        program = programs.get(row["program_id"])
        if program is None:
            errors.append(f"publication audit references missing program: {row['program_id']}")
            continue
        expected = "included" if program["inclusion_status"] == "included" else "held"
        if row["disposition"] != expected:
            errors.append(f"publication disposition disagrees with inclusion status: {row['program_id']}")
        if row["evidence_source_id"] not in sources:
            errors.append(f"publication audit source missing: {row['program_id']}")
        if not row["audit_finding"] or not row["publication_boundary"]:
            errors.append(f"publication audit rationale missing: {row['program_id']}")
    for program in programs.values():
        if program["inclusion_status"] == "needs_review" and program["program_id"] not in audited:
            errors.append(f"provisional program lacks publication disposition: {program['program_id']}")
    held_ids = {program_id for program_id, program in programs.items() if program["inclusion_status"] == "needs_review"}
    audited_held_ids = {row["program_id"] for row in program_audit if row["disposition"] == "held"}
    if len(held_ids) != 9 or held_ids != audited_held_ids:
        errors.append("nine held programs must match the publication-disposition ledger exactly")
    for row in outcomes:
        program = programs[row["program_id"]]
        if program["inclusion_status"] == "included" and row["primary_reason"] == "1":
            if row["event_type"] == "unknown" or row["confidence"] in {"", "unknown"}:
                errors.append(f"headline reason is unresolved: {row['outcome_event_id']}")
        if program["inclusion_status"] == "included" and not sources[row["source_id"]]["url"].startswith("https://"):
            errors.append(f"headline outcome has no HTTPS source: {row['outcome_event_id']}")
    if any(row["trial_id"] == "NCT00627627" for row in trials):
        errors.append("retaspimycin trial NCT00627627 remains in tanespimycin pilot")
    if not any(row["trial_id"] == "NCT00773344" and row["program_id"] == "PRG-tanespimycin-solid-tumor" for row in trials):
        errors.append("corrected tanespimycin trial missing")
    brivanib_program = programs.get("PRG-brivanib-hcc")
    brisk_aps = next((row for row in trials if row["trial_id"] == "NCT01108705"), None)
    brisk_aps_event = next((row for row in outcomes if row["outcome_event_id"] == "OUT-NCT01108705"), None)
    brisk_ps_event = next((row for row in outcomes if row["outcome_event_id"] == "OUT-NCT00825955"), None)
    if not brivanib_program or brivanib_program["inclusion_status"] != "needs_review":
        errors.append("brivanib HCC must remain held while BRISK-APS stopping cause is unresolved")
    if not brisk_aps or brisk_aps["program_id"] != "PRG-brivanib-hcc" or brisk_aps["recruitment_status"] != "terminated":
        errors.append("BRISK-APS must remain a separate terminated HCC trial")
    if not brisk_aps_event or any((
        brisk_aps_event["program_id"] != "PRG-brivanib-hcc",
        brisk_aps_event["event_type"] != "unknown",
        brisk_aps_event["primary_reason"] != "0",
        brisk_aps_event["stated_or_inferred"] != "unknown",
        brisk_aps_event["source_id"] != "SRC-CTG-brivanib",
    )):
        errors.append("BRISK-APS stopping cause must remain explicitly unknown and trial-specific")
    if not brisk_ps_event or brisk_ps_event["program_id"] != "PRG-brivanib-hcc" or brisk_ps_event["event_type"] != "endpoint_failure":
        errors.append("published BRISK-PS endpoint result must remain a separate trial event")

    result: dict[str, object] = {
        "status": "pass" if not errors else "fail",
        "audited_target_classes": len(target_audit),
        "explicitly_unresolved_target_classes": sum(r["audited_group"] == "Unresolved" for r in target_audit),
        "audited_provisional_programs": len(program_audit),
        "held_provisional_programs": sum(r["disposition"] == "held" for r in program_audit),
        "errors": errors,
    }
    return result


def main() -> None:
    result = audit()
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "publication-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
