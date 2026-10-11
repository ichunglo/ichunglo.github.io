"""Cache one verified ClinicalTrials.gov v2 study for pilot evidence intake."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tmp" / "clinicaltrials-candidates"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nct_id", help="NCT identifier, for example NCT01204749")
    args = parser.parse_args()
    nct_id = args.nct_id.upper()
    if not re.fullmatch(r"NCT\d{8}", nct_id):
        parser.error("Expected an NCT identifier followed by eight digits")
    with urlopen(f"https://clinicaltrials.gov/api/v2/studies/{nct_id}", timeout=20) as response:
        study = json.load(response)
    returned_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
    if returned_id != nct_id:
        raise ValueError(f"Registry returned {returned_id!r} for {nct_id}")
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{nct_id}.json"
    path.write_text(json.dumps(study, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
