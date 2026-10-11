"""Add the first registry-backed clinical pilot seed.

Historical bootstrap only. This creates 10 seed records but is deliberately
disabled after the publication audit because its placeholder evidence would
overwrite verified clinical curation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
GENERATED = ROOT / "data" / "generated"
TODAY = "2026-10-02"


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write(name: str, rows: list[dict[str, str]]) -> None:
    path = DATA / name
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def upsert(rows: list[dict[str, str]], new_rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    existing = {row[key]: row for row in rows}
    for row in new_rows:
        existing[row[key]] = row
    return list(existing.values())


def main() -> None:
    if (DATA / "publication-program-audit.csv").exists():
        raise SystemExit("Historical seed is disabled after publication audit; rerunning it would overwrite verified clinical curation.")
    targets = read("targets.csv")
    drugs = read("drugs.csv")
    sources = read("sources.csv")
    sponsors = read("sponsors.csv")
    programs = read("programs.csv")
    trials = read("trials.csv")
    outcomes = read("outcomes.csv")

    targets = upsert(targets, [
        {"target_id": "TGT-p56817-1", "preferred_name": "Beta-secretase 1", "gene_symbol": "BACE1", "uniprot_accession": "P56817", "organism_id": "1", "target_status": "confirmed", "landscape_scope": "clinical_only", "protein_group": "Enzymes", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "clinical pilot"},
        {"target_id": "TGT-p51451-1", "preferred_name": "Bruton tyrosine kinase", "gene_symbol": "BTK", "uniprot_accession": "P51451", "organism_id": "1", "target_status": "confirmed", "landscape_scope": "clinical_only", "protein_group": "Enzymes", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "clinical pilot"},
        {"target_id": "TGT-p11597-1", "preferred_name": "Cholesteryl ester transfer protein", "gene_symbol": "CETP", "uniprot_accession": "P11597", "organism_id": "1", "target_status": "confirmed", "landscape_scope": "clinical_only", "protein_group": "Enzymes", "target_type": "", "complex_description": "", "paper_target_name": "", "paper_source_row": "clinical pilot"},
    ], "target_id")

    drug_specs = [
        ("verubecestat", "small_molecule"), ("semagacestat", "small_molecule"), ("dalcetrapib", "small_molecule"),
        ("torcetrapib", "small_molecule"), ("evobrutinib", "small_molecule"), ("olaratumab", "biologic"),
        ("iniparib", "small_molecule"), ("atrasentan", "small_molecule"), ("lanabecestat", "small_molecule"),
        ("tanespimycin", "small_molecule"),
    ]
    drug_rows = []
    for name, modality in drug_specs:
        drug_rows.append({"drug_id": f"DRG-{name}", "generic_name": name, "preferred_name": name, "modality": modality, "chemical_or_biologic_id": "", "cas_registration_year": "", "atc_code": "", "source_name": "clinical pilot"})
    drugs = upsert(drugs, drug_rows, "drug_id")

    source_rows = [
        {"source_id": "SRC-CTG-verubecestat", "source_type": "trial_registry", "title": "ClinicalTrials.gov verubecestat pivotal study", "publisher": "ClinicalTrials.gov", "url": "https://clinicaltrials.gov/study/NCT01739348", "retrieval_date": TODAY, "citation": "NCT01739348", "source_priority": "1", "notes": "Registry status and phase"},
        {"source_id": "SRC-MERCK-verubecestat", "source_type": "company_disclosure", "title": "Merck verubecestat APECS discontinuation", "publisher": "Merck", "url": "https://www.merck.com/news/merck-announces-discontinuation-of-apecs-study-evaluating-verubecestat-mk-8931-for-the-treatment-of-people-with-prodromal-alzheimers-disease/", "retrieval_date": TODAY, "citation": "Merck announcement", "source_priority": "2", "notes": "Discontinuation rationale requires final curation"},
        {"source_id": "SRC-NEJM-semagacestat", "source_type": "peer_reviewed", "title": "A Phase 3 Trial of Semagacestat for Treatment of Alzheimer's Disease", "publisher": "New England Journal of Medicine", "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa1210951", "retrieval_date": TODAY, "citation": "NEJMoa1210951", "source_priority": "1", "notes": "Efficacy and safety outcome evidence"},
        {"source_id": "SRC-NEJM-dalcetrapib", "source_type": "peer_reviewed", "title": "Effects of Dalcetrapib in Patients with a Recent Acute Coronary Syndrome", "publisher": "New England Journal of Medicine", "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa1206797", "retrieval_date": TODAY, "citation": "NEJMoa1206797", "source_priority": "1", "notes": "Futility termination and efficacy outcome"},
        {"source_id": "SRC-NEJM-torcetrapib", "source_type": "peer_reviewed", "title": "Effects of Torcetrapib in Patients at High Risk for Coronary Events", "publisher": "New England Journal of Medicine", "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa0706628", "retrieval_date": TODAY, "citation": "NEJMoa0706628", "source_priority": "1", "notes": "Safety termination and mortality outcome"},
    ]
    sources = upsert(sources, source_rows, "source_id")

    sponsor_rows = [{"sponsor_id": f"SPN-{name}", "sponsor_name": sponsor, "sponsor_type": "industry"} for name, sponsor in [
        ("verubecestat", "Merck"), ("semagacestat", "Eli Lilly"), ("dalcetrapib", "Roche"), ("torcetrapib", "Pfizer"),
        ("evobrutinib", "Merck KGaA"), ("olaratumab", "Eli Lilly"), ("iniparib", "Sanofi"), ("atrasentan", "AbbVie"),
        ("lanabecestat", "AstraZeneca"), ("tanespimycin", "Bristol Myers Squibb"),
    ]]
    sponsors = upsert(sponsors, sponsor_rows, "sponsor_id")

    specs = [
        ("PRG-verubecestat-ad", "DRG-verubecestat", "SPN-verubecestat", "Alzheimer's disease", "TGT-p56817-1", "phase_3", "NCT01739348", "PHASE2|PHASE3", "TERMINATED", "unknown", "unknown", "SRC-CTG-verubecestat"),
        ("PRG-semagacestat-ad", "DRG-semagacestat", "SPN-semagacestat", "Alzheimer's disease", "TGT-p49768-1", "phase_3", "NCT01035138", "PHASE3", "COMPLETED", "endpoint_failure", "stated", "SRC-NEJM-semagacestat"),
        ("PRG-dalcetrapib-cv", "DRG-dalcetrapib", "SPN-dalcetrapib", "coronary artery disease", "TGT-p11597-1", "phase_3", "NCT00658515", "PHASE3", "COMPLETED", "endpoint_failure", "stated", "SRC-NEJM-dalcetrapib"),
        ("PRG-torcetrapib-cv", "DRG-torcetrapib", "SPN-torcetrapib", "cardiovascular disease", "TGT-p11597-1", "phase_3", "NCT00134264", "PHASE3", "TERMINATED", "safety_failure", "stated", "SRC-NEJM-torcetrapib"),
        ("PRG-evobrutinib-ms", "DRG-evobrutinib", "SPN-evobrutinib", "relapsing multiple sclerosis", "TGT-p51451-1", "phase_3", "NCT04032171", "PHASE3", "TERMINATED", "unknown", "unknown", "SRC-CTG-evobrutinib"),
        ("PRG-olaratumab-sts", "DRG-olaratumab", "SPN-olaratumab", "soft tissue sarcoma", "TGT-p16234-1", "phase_3", "NCT02451943", "PHASE3", "COMPLETED", "endpoint_failure", "stated", "SRC-CTG-olaratumab"),
        ("PRG-iniparib-tnbc", "DRG-iniparib", "SPN-iniparib", "triple-negative breast cancer", "TGT-p09874-1", "phase_3", "NCT00938652", "PHASE3", "COMPLETED", "endpoint_failure", "stated", "SRC-CTG-iniparib"),
        ("PRG-atrasentan-prostate", "DRG-atrasentan", "SPN-atrasentan", "metastatic prostate cancer", "TGT-p25101-1", "phase_3", "NCT00134056", "PHASE3", "COMPLETED", "endpoint_failure", "unknown", "SRC-CTG-atrasentan"),
        ("PRG-lanabecestat-ad", "DRG-lanabecestat", "SPN-lanabecestat", "Alzheimer's disease", "TGT-p56817-1", "phase_3", "NCT02783573", "PHASE3", "TERMINATED", "endpoint_failure", "unknown", "SRC-CTG-lanabecestat"),
        ("PRG-tanespimycin-solid-tumor", "DRG-tanespimycin", "SPN-tanespimycin", "advanced solid tumors", "TGT-p07900-1", "phase_2", "NCT00627627", "PHASE1|PHASE2", "WITHDRAWN", "unknown", "unknown", "SRC-CTG-tanespimycin"),
    ]

    extra_sources = []
    for program_id, drug_id, sponsor_id, indication, target_id, status, nct, phase_text, trial_status, outcome_type, stated, source_id in specs:
        if source_id not in {row["source_id"] for row in sources}:
            extra_sources.append({"source_id": source_id, "source_type": "trial_registry", "title": f"ClinicalTrials.gov {nct}", "publisher": "ClinicalTrials.gov", "url": f"https://clinicaltrials.gov/study/{nct}", "retrieval_date": TODAY, "citation": nct, "source_priority": "1", "notes": "Registry status and phase"})
        programs = upsert(programs, [{"program_id": program_id, "drug_id": drug_id, "sponsor_id": sponsor_id, "development_name": "", "indication_name": indication, "modality": next(row["modality"] for row in drugs if row["drug_id"] == drug_id), "lifecycle_status": status, "primary_target_id": target_id, "target_status": "unclear" if drug_id == "DRG-iniparib" else "confirmed", "inclusion_status": "needs_review" if outcome_type == "unknown" else "included", "first_known_date": "", "last_verified_date": TODAY, "notes": "Pilot seed; one representative trial linked"}], "program_id")
        trials = upsert(trials, [{"trial_id": nct, "program_id": program_id, "registry_name": "ClinicalTrials.gov", "registry_identifier": nct, "phase": "phase_3" if "PHASE3" in phase_text else "phase_2", "recruitment_status": trial_status.lower(), "start_date": "", "primary_completion_date": "", "study_completion_date": "", "primary_endpoint_result": ""}], "trial_id")
        outcomes = upsert(outcomes, [{"outcome_event_id": f"OUT-{program_id}", "program_id": program_id, "event_date": "", "event_type": outcome_type, "primary_reason": "1", "stated_or_inferred": stated, "confidence": "medium" if stated == "stated" else "unknown", "description": "Pilot seed; verify against full registry record and primary source.", "source_id": source_id}], "outcome_event_id")
    sources = upsert(sources, extra_sources, "source_id")

    write("targets.csv", targets)
    write("drugs.csv", drugs)
    write("sources.csv", sources)
    write("sponsors.csv", sponsors)
    write("programs.csv", programs)
    write("trials.csv", trials)
    write("outcomes.csv", outcomes)

    GENERATED.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"seed_programs": len(specs), "total_programs": len(programs), "total_trials": len(trials), "total_outcomes": len(outcomes)}, indent=2))


if __name__ == "__main__":
    main()
