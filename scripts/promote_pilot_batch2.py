"""Promote a registry-linked, reason-unresolved clinical batch."""

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
        w.writeheader(); w.writerows(rows)


def upsert(rows, new_rows, key):
    result = {r[key]: r for r in rows}
    result.update({r[key]: r for r in new_rows})
    return list(result.values())


def main():
    targets, drugs, sources, sponsors = (read(x) for x in ["targets.csv", "drugs.csv", "sources.csv", "sponsors.csv"])
    programs, trials, outcomes = (read(x) for x in ["programs.csv", "trials.csv", "outcomes.csv"])

    targets = upsert(targets, [
        {"target_id": "TGT-q9nq94-clinical", "preferred_name": "Glycoprotein NMB", "gene_symbol": "GPNMB", "uniprot_accession": "Q9NQ94", "organism_id": "1", "target_status": "unclear", "landscape_scope": "clinical_only", "protein_group": "Other proteins", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
        {"target_id": "TGT-p53350-clinical", "preferred_name": "Serine/threonine-protein kinase PLK1", "gene_symbol": "PLK1", "uniprot_accession": "P53350", "organism_id": "1", "target_status": "unclear", "landscape_scope": "clinical_only", "protein_group": "Enzymes", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"},
    ], "target_id")

    specs = [
        ("PRG-brivanib-hcc", "brivanib", "Brivanib", "SPN-brivanib", "hepatocellular carcinoma", "TGT-p35968-1", "phase_3", "NCT01108705"),
        ("PRG-linifanib-hcc", "linifanib", "Linifanib", "SPN-linifanib", "hepatocellular carcinoma", "TGT-p35968-1", "phase_3", "NCT01009593"),
        ("PRG-motesanib-cancer", "motesanib", "Motesanib", "SPN-motesanib", "advanced solid tumors", "TGT-p35968-1", "phase_2", "NCT00360867"),
        ("PRG-entospletinib-hematology", "entospletinib", "Entospletinib", "SPN-entospletinib", "relapsed hematologic malignancy", "TGT-p43405-1", "phase_2", "NCT01799889"),
        ("PRG-depatuxizumab-gbm", "depatuxizumab mafodotin", "Depatuxizumab mafodotin", "SPN-depatuxizumab", "glioblastoma", "TGT-p00533-1", "phase_3", "NCT03419403"),
        ("PRG-glembatumumab-lung", "glembatumumab", "Glembatumumab vedotin", "SPN-glembatumumab", "squamous cell lung cancer", "TGT-q9nq94-clinical", "phase_2", "NCT02713828"),
        ("PRG-rigosertib-myelofibrosis", "rigosertib", "Rigosertib", "SPN-rigosertib", "myelofibrosis", "TGT-p53350-clinical", "phase_2", "NCT02730884"),
        ("PRG-tivantinib-cancer", "tivantinib", "Tivantinib", "SPN-tivantinib", "advanced solid tumors", "TGT-p08581-1", "phase_2", "NCT01055067"),
        ("PRG-siltuximab-myeloma", "siltuximab", "Siltuximab", "SPN-siltuximab", "multiple myeloma", "TGT-p05231-1", "phase_3", "NCT01266811"),
        ("PRG-saracatinib-prostate", "saracatinib", "Saracatinib", "SPN-saracatinib", "prostate cancer", "TGT-p12931-1", "phase_2", "NCT00513071"),
    ]
    for program_id, generic, preferred, sponsor_id, indication, target_id, phase, nct in specs:
        modality = "biologic" if generic == "siltuximab" else "small_molecule"
        drug_id = f"DRG-{generic}"
        drugs = upsert(drugs, [{"drug_id": drug_id, "generic_name": generic, "preferred_name": preferred, "modality": modality, "chemical_or_biologic_id": "", "cas_registration_year": "", "atc_code": "", "source_name": "clinical pilot"}], "drug_id")
        sponsors = upsert(sponsors, [{"sponsor_id": sponsor_id, "sponsor_name": sponsor_id.replace("SPN-", "").replace("-", " "), "sponsor_type": "industry"}], "sponsor_id")
        programs = upsert(programs, [{"program_id": program_id, "drug_id": drug_id, "sponsor_id": sponsor_id, "development_name": "", "indication_name": indication, "modality": modality, "lifecycle_status": phase, "primary_target_id": target_id, "target_status": "unclear", "inclusion_status": "needs_review", "first_known_date": "", "last_verified_date": TODAY, "notes": "Registry-linked promotion; target and outcome evidence require manual review."}], "program_id")
        trials = upsert(trials, [{"trial_id": nct, "program_id": program_id, "registry_name": "ClinicalTrials.gov", "registry_identifier": nct, "phase": phase, "recruitment_status": "terminated_or_completed", "start_date": "", "primary_completion_date": "", "study_completion_date": "", "primary_endpoint_result": ""}], "trial_id")
        source_id = f"SRC-CTG-{generic.replace(' ', '-')}"
        sources = upsert(sources, [{"source_id": source_id, "source_type": "trial_registry", "title": f"ClinicalTrials.gov {nct}", "publisher": "ClinicalTrials.gov", "url": f"https://clinicaltrials.gov/study/{nct}", "retrieval_date": TODAY, "citation": nct, "source_priority": "1", "notes": "Registry status and phase; outcome reason unresolved"}], "source_id")
        outcomes = upsert(outcomes, [{"outcome_event_id": f"OUT-{program_id}", "program_id": program_id, "event_date": "", "event_type": "unknown", "primary_reason": "1", "stated_or_inferred": "unknown", "confidence": "unknown", "description": "Outcome reason not yet curated from primary efficacy, safety, or regulatory evidence.", "source_id": source_id}], "outcome_event_id")

    for name, rows in [("targets.csv", targets), ("drugs.csv", drugs), ("sources.csv", sources), ("sponsors.csv", sponsors), ("programs.csv", programs), ("trials.csv", trials), ("outcomes.csv", outcomes)]:
        write(name, rows)
    print(json.dumps({"promoted": len(specs), "total_programs": len(programs), "total_trials": len(trials), "total_outcomes": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
