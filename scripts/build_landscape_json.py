"""Build browser-ready JSON from the curated CSV layer."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from recent_target_analysis import build as build_recent_target_analysis
from recent_investigational_analysis import build as build_recent_investigational_analysis
from investigational_first_trial_review import validate as validate_first_trial_reviews
from investigational_pilot_rules import date_bounds


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"
GENERATED = ROOT / "data" / "generated"
INTAKE = ROOT / "data" / "intake"


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_optional_intake(name: str) -> list[dict[str, str]]:
    path = INTAKE / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    baseline = json.loads((GENERATED / "baseline-summary.json").read_text(encoding="utf-8"))
    drug_targets = read("drug-targets.csv")
    sources = read("sources.csv")
    programs = read("programs.csv")
    fda_indications = read("fda-approved-indications.csv")
    fda_review_ledger_path = GENERATED / "fda-review-ledger.csv"
    fda_review_ledger = []
    if fda_review_ledger_path.exists():
        with fda_review_ledger_path.open(encoding="utf-8", newline="") as handle:
            fda_review_ledger = list(csv.DictReader(handle))
    as_of_date = max(
        [baseline["as_of_date"]]
        + [row["retrieval_date"] for row in sources if row["retrieval_date"]]
        + [row["last_verified_date"] for row in programs if row["last_verified_date"]]
        + [row["verified_date"] for row in fda_indications if row["verified_date"]]
    )
    metrics = dict(baseline["counts"])
    # Preserve paper-comparable baseline counts while exposing the complete
    # normalized relationship count after clinical and supplemental links are
    # added to the release tables.
    metrics["drug_target_relationships"] = len(drug_targets)
    coverage_report_path = GENERATED / "target-coverage-report.json"
    coverage_report = json.loads(coverage_report_path.read_text(encoding="utf-8")) if coverage_report_path.exists() else {}
    pilot_dir = ROOT / "data" / "investigational-pilot"
    pilot_candidates_path = pilot_dir / "chembl-pilot-candidates.csv"
    pilot_summary_path = pilot_dir / "chembl-pilot-intake-summary.json"
    pilot_candidates = []
    if pilot_candidates_path.exists():
        with pilot_candidates_path.open(encoding="utf-8", newline="") as handle:
            pilot_candidates = list(csv.DictReader(handle))
    pilot_summary = json.loads(pilot_summary_path.read_text(encoding="utf-8")) if pilot_summary_path.exists() else {}
    reviewed_path = DATA / "investigational-pilot-reviewed.csv"
    pilot_reviewed = []
    if reviewed_path.exists():
        with reviewed_path.open(encoding="utf-8", newline="") as handle:
            pilot_reviewed = list(csv.DictReader(handle))
    pilot_review_queue = []
    review_queue_path = pilot_dir / "bulk-drug-review-queue.csv"
    if review_queue_path.exists():
        with review_queue_path.open(encoding="utf-8", newline="") as handle:
            pilot_review_queue = list(csv.DictReader(handle))
    pilot_issues = []
    issues_path = DATA / "investigational-pilot-evidence-issues.csv"
    if issues_path.exists():
        with issues_path.open(encoding="utf-8", newline="") as handle:
            pilot_issues = list(csv.DictReader(handle))
    pilot_studies = []
    studies_path = DATA / "investigational-pilot-study-evidence.csv"
    if studies_path.exists():
        with studies_path.open(encoding="utf-8", newline="") as handle:
            pilot_studies = list(csv.DictReader(handle))
    first_trial_path = DATA / "investigational-pilot-first-trial-review.csv"
    pilot_first_trials = []
    if first_trial_path.exists():
        with first_trial_path.open(encoding="utf-8", newline="") as handle:
            pilot_first_trials = list(csv.DictReader(handle))
        errors = validate_first_trial_reviews(pilot_first_trials, pilot_reviewed, pilot_issues)
        if errors:
            raise ValueError(f"Invalid first-trial reviews: {errors}")
    broad_path = ROOT / 'data' / 'investigational-landscape' / 'source-mechanisms.csv'
    broad_summary_path = broad_path.with_name('source-mechanisms-summary.json')
    broad = []
    broad_summary = {}
    if broad_path.exists() and broad_summary_path.exists():
        broad_summary = json.loads(broad_summary_path.read_text(encoding='utf-8'))
        if hashlib.sha256(broad_path.read_bytes()).hexdigest() != broad_summary.get('normalized_csv_sha256'):
            raise ValueError('Bulk mechanism CSV does not match its summary checksum')
        fields = ('target_id', 'target_gene', 'target_name', 'drug_chembl_id', 'drug_name', 'max_phase_source', 'mechanism_id', 'mechanism', 'source_url')
        with broad_path.open(encoding='utf-8', newline='') as handle:
            broad = [{field: row[field] for field in fields} for row in csv.DictReader(handle)]
        broad_summary = {key: value for key, value in broad_summary.items() if key != 'snapshot_pages'}
    registry_index_path = broad_path.with_name('registry-drug-index.json')
    registry_index = json.loads(registry_index_path.read_text(encoding='utf-8')) if registry_index_path.exists() else {}
    if registry_index and hashlib.sha256(broad_path.with_name('registry-candidates.sqlite').read_bytes()).hexdigest() != registry_index.get('database_sha256'):
        raise ValueError('Registry index is stale; rebuild it from registry-candidates.sqlite')
    triage_path = broad_path.with_name('history-triage.csv')
    history_triage = []
    if triage_path.exists():
        triage_summary = json.loads(triage_path.with_name('history-triage-summary.json').read_text(encoding='utf-8'))
        if hashlib.sha256(broad_path.with_name('registry-candidates.sqlite').read_bytes()).hexdigest() != triage_summary['source_database_sha256']:
            raise ValueError('Historical review queue is stale; rebuild it from registry-candidates.sqlite')
        triage_fields = ('drug_chembl_id', 'preferred_name', 'candidate_phase_1_to_3_studies', 'candidate_studies_without_parseable_start', 'conflicting_study_observations', 'earliest_candidate_study_id', 'earliest_candidate_study_start', 'earliest_candidate_study_start_type')
        with triage_path.open(encoding='utf-8', newline='') as handle:
            history_triage = [{field: row[field] for field in triage_fields} for row in csv.DictReader(handle)]
    broad_fda_path = broad_path.with_name('fda-name-candidates.csv')
    broad_fda = []
    broad_fda_all = []
    if broad_fda_path.exists():
        crosswalk_summary = json.loads(broad_fda_path.with_name('fda-name-candidates-summary.json').read_text(encoding='utf-8'))
        crosswalk_inputs = {'mechanisms': broad_path, 'catalog': DATA / 'drugs.csv', 'indications': DATA / 'fda-approved-indications.csv', 'decisions': DATA / 'fda-review-decisions.csv'}
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != crosswalk_summary['input_sha256'][key] for key, path in crosswalk_inputs.items()):
            raise ValueError('FDA name crosswalk is stale; rebuild it from the current source inputs')
        with broad_fda_path.open(encoding='utf-8', newline='') as handle:
            broad_fda_all = list(csv.DictReader(handle))
            broad_fda = [row for row in broad_fda_all if row['candidate_fda_approval_date']]
    approvals = read("approvals.csv")
    targets = read("targets.csv")
    recent_investigational = None
    historical_db = broad_path.with_name('historical-evidence.sqlite')
    if broad and history_triage and historical_db.exists():
        database = sqlite3.connect(historical_db.as_uri() + '?mode=ro', uri=True)
        database.row_factory = sqlite3.Row
        try:
            metadata = dict(database.execute('SELECT key,value FROM metadata'))
            if metadata.get('mechanism_source_sha256') != hashlib.sha256(broad_path.read_bytes()).hexdigest() or metadata.get('registry_source_sha256') != hashlib.sha256(broad_path.with_name('registry-candidates.sqlite').read_bytes()).hexdigest():
                raise ValueError('Historical evidence database is stale; rebuild it before analysis')
            study_rows = [dict(row) for row in database.execute('''SELECT DISTINCT c.drug_chembl_id,c.nct_id,s.start_date,s.conditions_json
                FROM drug_study_candidate c JOIN study_observation s ON c.batch_id=s.batch_id AND c.nct_id=s.nct_id''')]
        finally:
            database.close()
        fda_application_path = GENERATED / 'fda-application-review-queue.csv'
        if not fda_application_path.exists() or not broad_fda_all:
            raise ValueError('FDA application and name-match candidates are required for the timeline check')
        with fda_application_path.open(encoding='utf-8', newline='') as handle:
            fda_applications = list(csv.DictReader(handle))
        clinical_evidence_path = DATA / 'investigational-fda-clinical-evidence.csv'
        fda_clinical_evidence = read('investigational-fda-clinical-evidence.csv') if clinical_evidence_path.exists() else []
        evidence_ids = [row['drug_chembl_id'] for row in fda_clinical_evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError('FDA clinical evidence contains duplicate drug identifiers')
        for row in fda_clinical_evidence:
            source = urlparse(row['source_url'])
            if not date_bounds(row['known_clinical_by_date']) or row['date_interpretation'] != 'upper_bound_inferred_not_start_date' or source.scheme != 'https' or source.hostname not in ('www.accessdata.fda.gov', 'accessdata.fda.gov'):
                raise ValueError(f'Invalid FDA clinical evidence: {row["drug_chembl_id"]}')
        recent_investigational = build_recent_investigational_analysis(broad, history_triage, study_rows, targets, drug_targets,
                                                                       fda_indications, read('fda-review-decisions.csv'), broad_fda_all, fda_applications, fda_clinical_evidence)
        recent_investigational['fda_application_queue_sha256'] = hashlib.sha256(fda_application_path.read_bytes()).hexdigest()
        recent_investigational['fda_application_snapshot_date'] = fda_applications[0].get('source_snapshot_date', '') if fda_applications else ''
        timeline_fields = ('drug_chembl_id', 'name', 'earliest_matched_study_start', 'earliest_study_id',
                           'candidate_fda_approval_date', 'fda_basis', 'fda_source_url',
                           'candidate_catalog_drug_id', 'clinical_evidence_by_date', 'clinical_evidence_date_interpretation',
                           'clinical_evidence_source_url', 'clinical_evidence_note', 'review_status')
        with broad_path.with_name('fda-timeline-review.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=timeline_fields)
            writer.writeheader()
            writer.writerows(recent_investigational['fda_timeline_flagged_drugs'])
    payload = {
        "release": {"version": baseline["release_version"], "as_of_date": as_of_date, "paper_baseline_date": baseline["as_of_date"], "source": baseline["source"]},
        "metrics": metrics,
        "targets": targets,
        "drugs": read("drugs.csv"),
        "drug_targets": drug_targets,
        "approvals": approvals,
        "fda_approved_indications": fda_indications,
        "fda_primary_indication_review": fda_review_ledger,
        "sources": sources,
        "programs": programs,
        "trials": read("trials.csv"),
        "outcomes": read("outcomes.csv"),
        "clinical_programs": programs,
        "evidence_review": read_optional_intake("pilot-evidence-review.csv"),
        "coverage_report": coverage_report,
        "investigational_pilot": {"candidates": pilot_candidates, "summary": pilot_summary, "reviewed_examples": pilot_reviewed, "review_queue": pilot_review_queue, "evidence_issues": pilot_issues, "reviewed_studies": pilot_studies, "first_trial_reviews": pilot_first_trials},
        "investigational_landscape_discovery": {"mechanisms": broad, "summary": broad_summary, "registry": registry_index, "history_triage": history_triage, "fda_name_candidates": broad_fda},
        "recent_target_analysis": build_recent_target_analysis(approvals, drug_targets, targets),
        "recent_investigational_analysis": recent_investigational,
        "notes": baseline["notes"],
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "landscape.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"targets": len(payload["targets"]), "programs": len(payload["programs"]), "trials": len(payload["trials"]), "outcomes": len(payload["outcomes"])}, indent=2))


if __name__ == "__main__":
    main()
