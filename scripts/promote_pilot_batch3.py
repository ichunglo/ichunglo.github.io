"""Promote the next distinct programs and attach additional registry trials."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
TODAY = "2026-10-02"


def read(name):
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (DATA / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def upsert(rows, new_rows, key):
    result = {r[key]: r for r in rows}
    result.update({r[key]: r for r in new_rows})
    return list(result.values())


def main():
    targets, drugs, sources, sponsors = (
        read(x) for x in ["targets.csv", "drugs.csv", "sources.csv", "sponsors.csv"]
    )
    programs, trials, outcomes = (
        read(x) for x in ["programs.csv", "trials.csv", "outcomes.csv"]
    )

    targets = upsert(targets, [
        {"target_id": "TGT-p37288-1", "preferred_name": "Vasopressin V1a receptor", "gene_symbol": "AVPR1A", "uniprot_accession": "P37288", "organism_id": "1", "target_status": "unclear", "landscape_scope": "core", "protein_group": "GPCRs", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
        {"target_id": "TGT-p25098-clinical", "preferred_name": "Platelet-activating factor acetylhydrolase IB subunit beta", "gene_symbol": "PLA2G7", "uniprot_accession": "Q15102", "organism_id": "1", "target_status": "unclear", "landscape_scope": "clinical_only", "protein_group": "Enzymes", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
        {"target_id": "TGT-unknown-pevonedistat", "preferred_name": "Pevonedistat primary target unresolved", "gene_symbol": "", "uniprot_accession": "", "organism_id": "1", "target_status": "unclear", "landscape_scope": "unresolved", "protein_group": "Unresolved", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
        {"target_id": "TGT-unknown-tarenflurbil", "preferred_name": "Tarenflurbil primary target unresolved", "gene_symbol": "", "uniprot_accession": "", "organism_id": "1", "target_status": "unclear", "landscape_scope": "unresolved", "protein_group": "Unresolved", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
    ], "target_id")

    new_programs = [
        ("PRG-balovaptan-asd", "balovaptan", "Balovaptan", "SPN-balovaptan", "autism spectrum disorder", "TGT-p37288-1", "phase_2", "NCT02901431"),
        ("PRG-darapladib-cardiovascular", "darapladib", "Darapladib", "SPN-darapladib", "coronary atherosclerosis", "TGT-p25098-clinical", "phase_3", "NCT01067339"),
        ("PRG-pevonedistat-nsclc", "pevonedistat", "Pevonedistat", "SPN-pevonedistat", "advanced non-small cell lung cancer", "TGT-unknown-pevonedistat", "phase_2", "NCT03228186"),
        ("PRG-tarenflurbil-ad", "tarenflurbil", "Tarenflurbil", "SPN-tarenflurbil", "Alzheimer disease", "TGT-unknown-tarenflurbil", "phase_3", "NCT00322036"),
    ]

    for program_id, generic, preferred, sponsor_id, indication, target_id, phase, nct in new_programs:
        drug_id = f"DRG-{generic}"
        drugs = upsert(drugs, [{"drug_id": drug_id, "generic_name": generic, "preferred_name": preferred, "modality": "small_molecule", "chemical_or_biologic_id": "", "cas_registration_year": "", "atc_code": "", "source_name": "clinical pilot"}], "drug_id")
        sponsors = upsert(sponsors, [{"sponsor_id": sponsor_id, "sponsor_name": sponsor_id.replace("SPN-", "").replace("-", " "), "sponsor_type": "industry"}], "sponsor_id")
        programs = upsert(programs, [{"program_id": program_id, "drug_id": drug_id, "sponsor_id": sponsor_id, "development_name": "", "indication_name": indication, "modality": "small_molecule", "lifecycle_status": phase, "primary_target_id": target_id, "target_status": "unclear", "inclusion_status": "needs_review", "first_known_date": "", "last_verified_date": TODAY, "notes": "Registry-linked promotion; primary target and outcome reason require manual review."}], "program_id")
        source_id = f"SRC-CTG-{generic.replace(' ', '-')}"
        sources = upsert(sources, [{"source_id": source_id, "source_type": "trial_registry", "title": f"ClinicalTrials.gov {nct}", "publisher": "ClinicalTrials.gov", "url": f"https://clinicaltrials.gov/study/{nct}", "retrieval_date": TODAY, "citation": nct, "source_priority": "1", "notes": "Registry status and phase; outcome reason unresolved"}], "source_id")
        trials = upsert(trials, [{"trial_id": nct, "program_id": program_id, "registry_name": "ClinicalTrials.gov", "registry_identifier": nct, "phase": phase, "recruitment_status": "terminated_or_completed", "start_date": "", "primary_completion_date": "", "study_completion_date": "", "primary_endpoint_result": ""}], "trial_id")
        outcomes = upsert(outcomes, [{"outcome_event_id": f"OUT-{program_id}", "program_id": program_id, "event_date": "", "event_type": "unknown", "primary_reason": "1", "stated_or_inferred": "unknown", "confidence": "unknown", "description": "Outcome reason not yet curated from primary efficacy, safety, or regulatory evidence.", "source_id": source_id}], "outcome_event_id")

    # Additional trials are linked to an existing drug program rather than counted as new programs.
    follow_on = [
        ("NCT03504917", "PRG-balovaptan-asd", "phase_3", "Balovaptan ASD open-label extension"),
        ("NCT03319537", "PRG-pevonedistat-nsclc", "phase_2", "Pevonedistat in mesothelioma"),
        ("NCT00937352", "PRG-bapineuzumab-ad", "phase_3", "Bapineuzumab long-term safety study"),
        ("NCT03114657", "PRG-crenezumab-ad", "phase_3", "Crenezumab prodromal-to-mild Alzheimer disease study"),
        ("NCT01253668", "PRG-brivanib-hcc", "phase_2", "Brivanib metastatic renal cell carcinoma study"),
        ("NCT02573324", "PRG-depatuxizumab-gbm", "phase_3", "Depatuxizumab mafodotin newly diagnosed glioblastoma study"),
    ]
    for nct, program_id, phase, label in follow_on:
        source_id = f"SRC-CTG-{nct}"
        sources = upsert(sources, [{"source_id": source_id, "source_type": "trial_registry", "title": f"ClinicalTrials.gov {nct}", "publisher": "ClinicalTrials.gov", "url": f"https://clinicaltrials.gov/study/{nct}", "retrieval_date": TODAY, "citation": nct, "source_priority": "1", "notes": "Additional registry-linked trial; outcome reason unresolved"}], "source_id")
        trials = upsert(trials, [{"trial_id": nct, "program_id": program_id, "registry_name": "ClinicalTrials.gov", "registry_identifier": nct, "phase": phase, "recruitment_status": "terminated_or_completed", "start_date": "", "primary_completion_date": "", "study_completion_date": "", "primary_endpoint_result": label}], "trial_id")
        outcomes = upsert(outcomes, [{"outcome_event_id": f"OUT-{nct}", "program_id": program_id, "event_date": "", "event_type": "unknown", "primary_reason": "1", "stated_or_inferred": "unknown", "confidence": "unknown", "description": "Outcome reason not yet curated for this additional trial.", "source_id": source_id}], "outcome_event_id")

    for name, rows in [("targets.csv", targets), ("drugs.csv", drugs), ("sources.csv", sources), ("sponsors.csv", sponsors), ("programs.csv", programs), ("trials.csv", trials), ("outcomes.csv", outcomes)]:
        write(name, rows)
    print(json.dumps({"new_programs": len(new_programs), "follow_on_trials": len(follow_on), "total_programs": len(programs), "total_trials": len(trials), "total_outcomes": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
