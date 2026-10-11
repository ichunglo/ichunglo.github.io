"""Validate the normalized CSV layer before JSON generation or publication."""

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


def unique(rows: list[dict[str, str]], field: str) -> bool:
    values = [row[field] for row in rows if row.get(field)]
    return len(values) == len(set(values))


def main() -> None:
    targets = read("targets.csv")
    drugs = read("drugs.csv")
    sponsors = read("sponsors.csv")
    links = read("drug-targets.csv")
    sources = read("sources.csv")
    programs = read("programs.csv")
    trials = read("trials.csv")
    outcomes = read("outcomes.csv")

    target_ids = {row["target_id"] for row in targets}
    drug_ids = {row["drug_id"] for row in drugs}
    sponsor_ids = {row["sponsor_id"] for row in sponsors}
    source_ids = {row["source_id"] for row in sources}
    errors: list[str] = []

    for name, rows, field in [
        ("targets", targets, "target_id"),
        ("drugs", drugs, "drug_id"),
        ("sponsors", sponsors, "sponsor_id"),
        ("drug-targets", links, "drug_target_id"),
        ("sources", sources, "source_id"),
        ("programs", programs, "program_id"),
        ("trials", trials, "trial_id"),
        ("outcomes", outcomes, "outcome_event_id"),
    ]:
        if not unique(rows, field):
            errors.append(f"duplicate {field} values in {name}.csv")

    for row in links:
        if row["drug_id"] not in drug_ids:
            errors.append(f"drug-target link references missing drug: {row['drug_id']}")
        if row["target_id"] not in target_ids:
            errors.append(f"drug-target link references missing target: {row['target_id']}")
        if row["target_role"] not in {"primary", "secondary"}:
            errors.append(f"invalid target role: {row['target_role']}")
        if row["source_id"] not in source_ids:
            errors.append(f"drug-target link references missing source: {row['source_id']}")
        if row["target_role"] == "primary" and row["moa_status"] == "unclear" and not row["target_id"].startswith("TGT-unknown-"):
            errors.append(f"unclear primary drug-target link names a protein: {row['drug_target_id']}")

    for row in programs:
        if row["drug_id"] not in drug_ids:
            errors.append(f"program references missing drug: {row['drug_id']}")
        if row["sponsor_id"] and row["sponsor_id"] not in sponsor_ids:
            errors.append(f"program references missing sponsor: {row['sponsor_id']}")
        if row["primary_target_id"] and row["primary_target_id"] not in target_ids:
            errors.append(f"program references missing target: {row['primary_target_id']}")
        if row["target_status"] not in {"confirmed", "unclear", "missing"}:
            errors.append(f"invalid program target status: {row['target_status']}")

    program_ids = {row["program_id"] for row in programs}
    for row in trials:
        if row["program_id"] not in program_ids:
            errors.append(f"trial references missing program: {row['program_id']}")
    for row in outcomes:
        if row["program_id"] not in program_ids:
            errors.append(f"outcome references missing program: {row['program_id']}")
        if row["source_id"] not in source_ids:
            errors.append(f"outcome references missing source: {row['source_id']}")

    links_by_pair: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in links:
        links_by_pair.setdefault((row["drug_id"], row["target_id"]), []).append(row)

    programs_missing_drug_target_link = [
        row["program_id"]
        for row in programs
        if row["primary_target_id"] and (row["drug_id"], row["primary_target_id"]) not in links_by_pair
    ]
    for program in programs:
        target_id = program["primary_target_id"]
        if not target_id:
            continue
        direct_links = links_by_pair.get((program["drug_id"], target_id), [])
        if not direct_links:
            errors.append(f"program has no primary drug-target link: {program['program_id']}")
            continue
        if len(direct_links) != 1 or direct_links[0]["target_role"] != "primary":
            errors.append(f"program primary target has ambiguous link role: {program['program_id']}")
        if direct_links[0]["moa_status"] != program["target_status"]:
            errors.append(f"program target status disagrees with primary link: {program['program_id']}")
        if target_id.startswith("TGT-unknown-") and (
            program["target_status"] != "unclear" or direct_links[0]["moa_status"] != "unclear"
        ):
            errors.append(f"unresolved program target is not labeled unclear: {program['program_id']}")
        if program["target_status"] == "unclear" and not target_id.startswith("TGT-unknown-"):
            errors.append(f"unclear program target names a protein: {program['program_id']}")

    unlinked_target_ids = sorted(target_ids - {row["target_id"] for row in links})
    for target_id in unlinked_target_ids:
        errors.append(f"target has no drug-target link: {target_id}")

    result = {
        "status": "pass" if not errors else "fail",
        "counts": {"targets": len(targets), "drugs": len(drugs), "drug_target_links": len(links), "programs": len(programs), "trials": len(trials), "outcomes": len(outcomes)},
        "programs_missing_drug_target_link": programs_missing_drug_target_link,
        "targets_without_drug_target_link": unlinked_target_ids,
        "errors": errors,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
