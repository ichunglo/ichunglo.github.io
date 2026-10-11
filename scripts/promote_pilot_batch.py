"""Promote a small, source-linked batch from the clinical review queue."""

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
    existing = {row[key]: row for row in rows}
    for row in new_rows:
        existing[row[key]] = row
    return list(existing.values())


def main() -> None:
    targets = read("targets.csv")
    drugs = read("drugs.csv")
    sources = read("sources.csv")
    sponsors = read("sponsors.csv")
    programs = read("programs.csv")
    trials = read("trials.csv")
    outcomes = read("outcomes.csv")

    targets = upsert(targets, [{"target_id": "TGT-q9y5n1-clinical", "preferred_name": "5-hydroxytryptamine receptor 6", "gene_symbol": "HTR6", "uniprot_accession": "Q9Y5N1", "organism_id": "1", "target_status": "unclear", "landscape_scope": "clinical_only", "protein_group": "GPCRs", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "pilot review"}], "target_id")

    specs = [
        ("PRG-bapineuzumab-ad", "bapineuzumab", "Bapineuzumab", "SPN-bapineuzumab", "Alzheimer's disease", "TGT-p05067-1", "phase_3", "NCT00667810", "TERMINATED", "endpoint_failure", "included", "SRC-NEJM-bapineuzumab"),
        ("PRG-crenezumab-ad", "crenezumab", "Crenezumab", "SPN-crenezumab", "Alzheimer's disease", "TGT-p05067-1", "phase_3", "NCT02670083", "TERMINATED", "endpoint_failure", "included", "SRC-PUBMED-crenezumab"),
        ("PRG-idalopirdine-ad", "idalopirdine", "Idalopirdine", "SPN-idalopirdine", "Alzheimer's disease", "TGT-q9y5n1-clinical", "phase_3", "NCT01955161", "COMPLETED", "endpoint_failure", "needs_review", "SRC-CTG-idalopirdine"),
        ("PRG-trebananib-ovarian", "trebananib", "Trebananib", "SPN-trebananib", "ovarian cancer", "TGT-o15123-1", "phase_3", "NCT01281254", "TERMINATED", "endpoint_failure", "needs_review", "SRC-CTG-trebananib"),
        ("PRG-rolofylline-heart-failure", "rolofylline", "Rolofylline", "SPN-rolofylline", "acute heart failure", "TGT-p30542-1", "phase_3", "NCT00328692", "COMPLETED", "endpoint_failure", "needs_review", "SRC-CTG-rolofylline"),
        ("PRG-onartuzumab-nsclc", "onartuzumab", "Onartuzumab", "SPN-onartuzumab", "non-small-cell lung cancer", "TGT-p08581-1", "phase_3", "NCT01456325", "COMPLETED", "endpoint_failure", "needs_review", "SRC-CTG-onartuzumab"),
        ("PRG-rovalpituzumab-sclc", "rovalpituzumab tesirine", "Rovalpituzumab tesirine", "SPN-rovalpituzumab", "small-cell lung cancer", "TGT-q9nyj7-1", "phase_3", "NCT03033511", "TERMINATED", "endpoint_failure", "needs_review", "SRC-CTG-rovalpituzumab"),
        ("PRG-solanezumab-ad", "solanezumab", "Solanezumab", "SPN-solanezumab", "Alzheimer's disease", "TGT-p05067-1", "phase_3", "NCT01900665", "COMPLETED", "endpoint_failure", "included", "SRC-NEJM-solanezumab"),
    ]

    for program_id, generic_name, preferred, sponsor_id, indication, target_id, status, nct, trial_status, outcome, inclusion, source_id in specs:
        actual_drug_id = f"DRG-{generic_name}"
        modality = "biologic" if preferred in {"Bapineuzumab", "Crenezumab", "Rovalpituzumab tesirine", "Solanezumab"} else "small_molecule"
        drugs = upsert(drugs, [{"drug_id": actual_drug_id, "generic_name": generic_name, "preferred_name": preferred, "modality": modality, "chemical_or_biologic_id": "", "cas_registration_year": "", "atc_code": "", "source_name": "clinical pilot"}], "drug_id")
        sponsors = upsert(sponsors, [{"sponsor_id": sponsor_id, "sponsor_name": sponsor_id.replace("SPN-", "").replace("-", " "), "sponsor_type": "industry"}], "sponsor_id")
        programs = upsert(programs, [{"program_id": program_id, "drug_id": actual_drug_id, "sponsor_id": sponsor_id, "development_name": "", "indication_name": indication, "modality": modality, "lifecycle_status": status, "primary_target_id": target_id, "target_status": "unclear" if inclusion == "needs_review" else "confirmed", "inclusion_status": inclusion, "first_known_date": "", "last_verified_date": TODAY, "notes": "Promoted pilot batch; verify all program-level evidence before publication."}], "program_id")
        trials = upsert(trials, [{"trial_id": nct, "program_id": program_id, "registry_name": "ClinicalTrials.gov", "registry_identifier": nct, "phase": "phase_3", "recruitment_status": trial_status.lower(), "start_date": "", "primary_completion_date": "", "study_completion_date": "", "primary_endpoint_result": ""}], "trial_id")
        outcomes = upsert(outcomes, [{"outcome_event_id": f"OUT-{program_id}", "program_id": program_id, "event_date": "", "event_type": outcome, "primary_reason": "1", "stated_or_inferred": "stated" if inclusion == "included" else "unknown", "confidence": "high" if inclusion == "included" else "unknown", "description": "Primary efficacy outcome did not support continued development; verify exact program-level wording.", "source_id": source_id}], "outcome_event_id")

    source_rows = [
        {"source_id": "SRC-NEJM-bapineuzumab", "source_type": "peer_reviewed", "title": "Two Phase 3 Trials of Bapineuzumab", "publisher": "New England Journal of Medicine", "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa1304839", "retrieval_date": TODAY, "citation": "NEJMoa1304839", "source_priority": "1", "notes": "Clinical efficacy and ARIA evidence"},
        {"source_id": "SRC-PUBMED-crenezumab", "source_type": "peer_reviewed", "title": "Evaluating the Safety and Efficacy of Crenezumab vs Placebo", "publisher": "JAMA", "url": "https://pubmed.ncbi.nlm.nih.gov/36121669/", "retrieval_date": TODAY, "citation": "PMID 36121669", "source_priority": "1", "notes": "Clinical efficacy evidence"},
        {"source_id": "SRC-NEJM-solanezumab", "source_type": "peer_reviewed", "title": "Trial of Solanezumab for Mild Dementia Due to Alzheimer's Disease", "publisher": "New England Journal of Medicine", "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa1705971", "retrieval_date": TODAY, "citation": "NEJMoa1705971", "source_priority": "1", "notes": "Clinical efficacy evidence"},
    ]
    for _, _, _, _, _, _, _, nct, _, _, _, source_id in specs:
        if source_id.startswith("SRC-CTG-"):
            source_rows.append({"source_id": source_id, "source_type": "trial_registry", "title": f"ClinicalTrials.gov {nct}", "publisher": "ClinicalTrials.gov", "url": f"https://clinicaltrials.gov/study/{nct}", "retrieval_date": TODAY, "citation": nct, "source_priority": "1", "notes": "Registry status and phase"})
    sources = upsert(sources, source_rows, "source_id")

    for name, rows in [("targets.csv", targets), ("drugs.csv", drugs), ("sources.csv", sources), ("sponsors.csv", sponsors), ("programs.csv", programs), ("trials.csv", trials), ("outcomes.csv", outcomes)]:
        write(name, rows)
    print(json.dumps({"promoted": len(specs), "total_programs": len(programs), "total_trials": len(trials), "total_outcomes": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
