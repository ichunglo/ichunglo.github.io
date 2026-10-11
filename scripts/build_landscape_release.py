"""Rebuild all derived landscape artifacts in the safe post-curation order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "build_pilot_evidence_review.py",
    "build_evidence_review_queue.py",
    "build_target_coverage_report.py",
    "build_landscape_json.py",
    "build_publication_figure.py",
    "validate_curated_data.py",
    "validate_publication_audit.py",
]


def main() -> None:
    for script in STEPS:
        print(f"==> {script}")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("Landscape release build: pass")


if __name__ == "__main__":
    main()
