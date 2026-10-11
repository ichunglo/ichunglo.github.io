"""Promote the remaining distinct registry candidates into the clinical pilot."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
TODAY = "2026-10-02"


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write(name: str, rows: list[dict[str, str]]) -> None:
    with (DATA / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def upsert(rows: list[dict[str, str]], new_rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    by_key = {row[key]: row for row in rows}
    by_key.update({row[key]: row for row in new_rows})
    return list(by_key.values())


def main() -> None:
    drugs, drug_targets, programs, trials, outcomes, sources = (
        read(name)
        for name in ["drugs.csv", "drug-targets.csv", "programs.csv", "trials.csv", "outcomes.csv", "sources.csv"]
    )

    additions = [
        {
            "program_id": "PRG-trebananib-ovarian",
            "generic": "trebananib",
            "preferred": "Trebananib (AMG 386)",
            "sponsor": "Amgen",
            "indication": "ovarian cancer",
            "target_id": "TGT-o15123-1",
            "target_status": "unclear",
            "phase": "phase_3",
            "ncts": ["NCT01204749", "NCT01281254", "NCT01493505"],
            "modality": "biologic",
        },
        {
            "program_id": "PRG-tideglusib-neurology",
            "generic": "tideglusib",
            "preferred": "Tideglusib",
            "sponsor": "Noscira",
            "indication": "neurologic disease",
            "target_id": "TGT-p49841-1",
            "target_status": "unclear",
            "phase": "phase_2",
            "ncts": ["NCT03692312", "NCT00948259", "NCT01350362"],
            "modality": "small_molecule",
        },
        {
            "program_id": "PRG-varespladib-cardiovascular",
            "generic": "varespladib",
            "preferred": "Varespladib",
            "sponsor": "Anthera Pharmaceuticals",
            "indication": "cardiovascular disease",
            "target_id": "TGT-p25098-clinical",
            "target_status": "unclear",
            "phase": "phase_2",
            "ncts": ["NCT01522196", "NCT00455546", "NCT00743925"],
            "modality": "small_molecule",
        },
    ]

    new_drugs = []
    new_links = []
    new_programs = []
    new_trials = []
    new_outcomes = []
    new_sources = []
    for item in additions:
        drug_id = f"DRG-{item['generic']}"
        sponsor_id = f"SPN-{item['generic']}"
        new_drugs.append({
            "drug_id": drug_id,
            "generic_name": item["generic"],
            "preferred_name": item["preferred"],
            "modality": item["modality"],
            "chemical_or_biologic_id": "",
            "cas_registration_year": "",
            "atc_code": "",
            "source_name": "clinical pilot",
        })
        new_links.append({
            "drug_target_id": f"DT-{drug_id.lower()}-{item['target_id'].lower()}",
            "drug_id": drug_id,
            "target_id": item["target_id"],
            "target_role": "primary",
            "moa_status": item["target_status"],
            "potency_value": "",
            "potency_unit": "",
            "potency_log10_molar": "",
            "evidence_grade": "clinical-pilot",
            "source_id": f"SRC-CTG-{item['generic']}",
        })
        new_sources.append({
            "source_id": f"SRC-CTG-{item['generic']}",
            "source_type": "trial_registry",
            "title": f"ClinicalTrials.gov registry evidence for {item['preferred']}",
            "publisher": "ClinicalTrials.gov",
            "url": f"https://clinicaltrials.gov/search?term={item['generic']}",
            "retrieval_date": TODAY,
            "citation": item["generic"],
            "source_priority": "1",
            "notes": "Registry-linked clinical pilot target relationship; outcome reason unresolved",
        })
        new_programs.append({
            "program_id": item["program_id"],
            "drug_id": drug_id,
            "sponsor_id": sponsor_id,
            "development_name": item["preferred"],
            "indication_name": item["indication"],
            "modality": item["modality"],
            "lifecycle_status": item["phase"],
            "primary_target_id": item["target_id"],
            "target_status": item["target_status"],
            "inclusion_status": "needs_review",
            "first_known_date": "",
            "last_verified_date": TODAY,
            "notes": "Registry-linked promotion; primary target and outcome reason require manual review.",
        })
        for nct in item["ncts"]:
            source_id = f"SRC-CTG-{nct}"
            new_sources.append({
                "source_id": source_id,
                "source_type": "trial_registry",
                "title": f"ClinicalTrials.gov {nct}",
                "publisher": "ClinicalTrials.gov",
                "url": f"https://clinicaltrials.gov/study/{nct}",
                "retrieval_date": TODAY,
                "citation": nct,
                "source_priority": "1",
                "notes": "Registry status and phase; outcome reason unresolved",
            })
            new_trials.append({
                "trial_id": nct,
                "program_id": item["program_id"],
                "registry_name": "ClinicalTrials.gov",
                "registry_identifier": nct,
                "phase": item["phase"],
                "recruitment_status": "terminated_or_completed",
                "start_date": "",
                "primary_completion_date": "",
                "study_completion_date": "",
                "primary_endpoint_result": "",
            })
            new_outcomes.append({
                "outcome_event_id": f"OUT-{nct}",
                "program_id": item["program_id"],
                "event_date": "",
                "event_type": "unknown",
                "primary_reason": "1",
                "stated_or_inferred": "unknown",
                "confidence": "unknown",
                "description": "Outcome reason not yet curated from primary efficacy, safety, or regulatory evidence.",
                "source_id": source_id,
            })

    drugs = upsert(drugs, new_drugs, "drug_id")
    drug_targets = upsert(drug_targets, new_links, "drug_target_id")
    programs = upsert(programs, new_programs, "program_id")
    trials = upsert(trials, new_trials, "trial_id")
    outcomes = upsert(outcomes, new_outcomes, "outcome_event_id")
    sources = upsert(sources, new_sources, "source_id")
    for name, rows in [("drugs.csv", drugs), ("drug-targets.csv", drug_targets), ("programs.csv", programs), ("trials.csv", trials), ("outcomes.csv", outcomes), ("sources.csv", sources)]:
        write(name, rows)
    print(json.dumps({"new_programs": len(new_programs), "new_trials": len(new_trials), "total_programs": len(programs), "total_trials": len(trials), "total_outcomes": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
