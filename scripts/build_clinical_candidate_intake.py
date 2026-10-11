"""Build an uncurated clinical-program candidate list from registry search results.

Candidates remain outside data/curated until target, program identity, and
outcome reasons are manually verified.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tmp" / "clinicaltrials-candidates"
OUT = ROOT / "data" / "intake" / "clinical-candidates.csv"


def main() -> None:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in sorted(RAW.glob("*.json")):
        search_term = path.stem.replace("_", " ")
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = []
        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            nct_id = identification.get("nctId", "")
            phases = design.get("phases", []) or []
            overall = status.get("overallStatus", "")
            if not nct_id or not any(p in {"PHASE2", "PHASE3"} for p in phases):
                continue
            if overall not in {"TERMINATED", "WITHDRAWN", "COMPLETED", "SUSPENDED"}:
                continue
            priority = {"TERMINATED": 0, "WITHDRAWN": 1, "SUSPENDED": 2, "COMPLETED": 3}.get(overall, 9)
            candidates.append((priority, "PHASE3" not in phases, nct_id, protocol))
        for _, _, nct_id, protocol in sorted(candidates)[:3]:
            if nct_id in seen:
                continue
            seen.add(nct_id)
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            design = protocol.get("designModule", {})
            sponsor = protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")
            conditions = protocol.get("conditionsModule", {}).get("conditions", []) or []
            rows.append({
                "candidate_id": f"CAND-{nct_id}",
                "search_term": search_term,
                "nct_id": nct_id,
                "title": identification.get("briefTitle", ""),
                "status": status.get("overallStatus", ""),
                "phases": "|".join(design.get("phases", []) or []),
                "sponsor": sponsor,
                "conditions": "|".join(conditions[:5]),
                "registry_url": f"https://clinicaltrials.gov/study/{nct_id}",
                "target_name": "",
                "failure_reason": "",
                "review_status": "needs_review",
                "notes": "Registry-discovered candidate; do not publish until target and outcome evidence are curated.",
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"candidate_count": len(rows), "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
