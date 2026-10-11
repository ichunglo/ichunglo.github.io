"""Extract registry evidence for manual curation of pilot outcome reasons."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tmp" / "clinicaltrials-candidates"
CURATED = ROOT / "data" / "curated"
OUT = ROOT / "data" / "intake" / "pilot-evidence-review.csv"


def load_trials():
    with (CURATED / "trials.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def registry_records():
    records = {}
    for path in sorted(RAW.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        studies = payload.get("studies")
        if not isinstance(studies, list):
            studies = [payload] if isinstance(payload.get("protocolSection"), dict) else []
        for study in studies:
            protocol = study.get("protocolSection", {})
            nct = protocol.get("identificationModule", {}).get("nctId")
            if nct:
                records[nct] = (path.name, protocol, "primary")
                for alias in protocol.get("identificationModule", {}).get("nctIdAliases", []) or []:
                    if alias.startswith("NCT"):
                        records[alias] = (path.name, protocol, "merged_alias")
    return records


def classify_reason(why_stopped: str):
    text = re.sub(r"\s+", " ", (why_stopped or "").strip())
    lower = text.lower()
    if not text:
        return "", "", "manual_review"
    if re.search(r"based on results of different study|similar hypothesis", lower):
        return "cross_study_decision", "stated", "high"
    if re.search(r"no beneficial information gained from continuing (?:long term follow up|ltfu)|closure of long term follow up", lower):
        return "followup_closure", "stated", "high"
    if re.search(r"unfavorable (?:risk-benefit|benefit-risk)", lower):
        return "risk_benefit_discontinuation", "stated", "high"
    if re.search(r"low rate of randomized patients|too few patients (?:were )?randomized|insufficient patients (?:were )?randomized", lower):
        return "lead_in_futility", "stated", "high"
    if re.search(r"no (clinical|statistical)(?: (?:or|and))? benefit|did not meet|failed to meet|lack of efficacy|lack of survival benefit|unlikely to meet .*primary (endpoint|objective)|futility|no beneficial information", lower):
        return "endpoint_failure", "stated", "high"
    if re.search(r"safety|adverse event|toxicity|tolerability", lower):
        return "safety", "stated", "high"
    if re.search(r"pharmacokinetic|pharmacodynamic|\bpk/pd\b", lower):
        return "pk_pd_failure", "stated", "high"
    if re.search(r"change in (the )?active comparator|change in comparator|comparator .* warranted", lower):
        return "trial_design_failure", "stated", "medium"
    if re.search(r"redirect focus of the indication|redirected focus|change in indication focus", lower):
        return "strategic_or_commercial", "stated", "medium"
    if re.search(r"at the request of the drug manufacturer|decided not to pursue|not to pursue additional research|administrative decision|change in company plans|company plans", lower):
        return "strategic_or_commercial", "stated", "medium"
    if re.search(r"recruitment|enroll|accrual", lower):
        return "recruitment", "stated", "high"
    if re.search(r"regulatory|fda|ema|approval", lower):
        return "regulatory", "stated", "high"
    if re.search(r"company discontinued|discontinued (the )?development|development .* discontinued|study drug|company decision|sponsor'?s decision|sponsor decision|sponsor terminated study agreement|amgen decision", lower):
        return "strategic_or_commercial", "stated", "medium"
    return "unknown", "stated", "low"


def main():
    records = registry_records()
    rows = []
    for trial in load_trials():
        nct = trial["trial_id"]
        source_file, protocol, registry_id_role = records.get(nct, ("", {}, "unmatched"))
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        outcomes = protocol.get("outcomesModule", {})
        why = status.get("whyStopped", "")
        reason, stated_or_inferred, confidence = classify_reason(why)
        primary = " | ".join(o.get("measure", "") for o in outcomes.get("primaryOutcomes", []) if o.get("measure"))
        rows.append({
            "trial_id": nct,
            "current_registry_id": identification.get("nctId", ""),
            "registry_id_role": registry_id_role,
            "program_id": trial["program_id"],
            "registry_title": identification.get("briefTitle", ""),
            "overall_status": status.get("overallStatus", ""),
            "phase": "|".join(design.get("phases", [])),
            "enrollment": str(design.get("enrollmentInfo", {}).get("count", "")),
            "why_stopped": why,
            "primary_outcomes": primary,
            "candidate_reason": reason,
            "stated_or_inferred": stated_or_inferred,
            "candidate_confidence": confidence,
            "source_url": f"https://clinicaltrials.gov/study/{nct}",
            "raw_source_file": source_file,
            "curation_status": "needs_review",
        })
    rows.sort(key=lambda r: r["trial_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row["candidate_reason"] or "no_registry_reason"] = counts.get(row["candidate_reason"] or "no_registry_reason", 0) + 1
    print(json.dumps({"rows": len(rows), "candidate_reason_counts": counts, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
