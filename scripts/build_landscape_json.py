"""Build browser-ready JSON from the curated CSV layer."""

from __future__ import annotations

import csv
import json
from pathlib import Path


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
    as_of_date = max(
        [baseline["as_of_date"]]
        + [row["retrieval_date"] for row in sources if row["retrieval_date"]]
        + [row["last_verified_date"] for row in programs if row["last_verified_date"]]
    )
    metrics = dict(baseline["counts"])
    # Preserve paper-comparable baseline counts while exposing the complete
    # normalized relationship count after clinical and supplemental links are
    # added to the release tables.
    metrics["drug_target_relationships"] = len(drug_targets)
    coverage_report_path = GENERATED / "target-coverage-report.json"
    coverage_report = json.loads(coverage_report_path.read_text(encoding="utf-8")) if coverage_report_path.exists() else {}
    payload = {
        "release": {"version": baseline["release_version"], "as_of_date": as_of_date, "paper_baseline_date": baseline["as_of_date"], "source": baseline["source"]},
        "metrics": metrics,
        "targets": read("targets.csv"),
        "drugs": read("drugs.csv"),
        "drug_targets": drug_targets,
        "approvals": read("approvals.csv"),
        "sources": sources,
        "programs": programs,
        "trials": read("trials.csv"),
        "outcomes": read("outcomes.csv"),
        "clinical_programs": programs,
        "evidence_review": read_optional_intake("pilot-evidence-review.csv"),
        "coverage_report": coverage_report,
        "notes": baseline["notes"],
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "landscape.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"targets": len(payload["targets"]), "programs": len(payload["programs"]), "trials": len(payload["trials"]), "outcomes": len(payload["outcomes"])}, indent=2))


if __name__ == "__main__":
    main()
