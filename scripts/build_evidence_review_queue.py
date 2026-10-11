"""Prioritize clinical evidence records that need manual outcome review."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "intake" / "pilot-evidence-review.csv"
OUTPUT = ROOT / "data" / "intake" / "pilot-evidence-review-queue.csv"
OUTCOMES = ROOT / "data" / "curated" / "outcomes.csv"


def main() -> None:
    with INPUT.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with OUTCOMES.open(encoding="utf-8", newline="") as handle:
        outcomes = list(csv.DictReader(handle))
    explicit_trial_ids = {
        row["outcome_event_id"].removeprefix("OUT-")
        for row in outcomes
        if row.get("outcome_event_id", "").startswith("OUT-NCT")
    }
    curated_trial_ids = {
        row["outcome_event_id"].removeprefix("OUT-")
        for row in outcomes
        if row.get("outcome_event_id", "").startswith("OUT-NCT")
        and (
            row.get("event_type") not in {"", "unknown"}
            or (row.get("primary_reason") == "0" and row.get("confidence") == "high" and row.get("source_id"))
        )
    }
    curated_program_ids = {
        row.get("program_id", "")
        for row in outcomes
        if row.get("outcome_event_id", "").startswith("OUT-PRG-") and row.get("event_type") not in {"", "unknown"}
    }
    queue = []
    for row in rows:
        if row.get("candidate_reason") or row.get("why_stopped"):
            continue
        trial_id = row.get("trial_id", "")
        if trial_id in curated_trial_ids:
            continue
        # A broad program decision cannot resolve an explicitly unknown trial event.
        if trial_id not in explicit_trial_ids and row.get("program_id") in curated_program_ids:
            continue
        phase = row.get("phase", "")
        status = row.get("overall_status", "")
        if not row.get("registry_title"):
            priority = "P1"
            action = "Retrieve registry payload and primary outcome evidence"
        elif "PHASE3" in phase and status in {"TERMINATED", "WITHDRAWN"}:
            priority = "P1"
            action = "Check primary publication, regulatory record, or sponsor disclosure for failure reason"
        elif "PHASE3" in phase:
            priority = "P2"
            action = "Check primary publication for endpoint result and target-biology interpretation"
        else:
            priority = "P3"
            action = "Review primary outcome and classify only if evidence supports a reason"
        queue.append({
            "review_priority": priority,
            "trial_id": row.get("trial_id", ""),
            "program_id": row.get("program_id", ""),
            "phase": phase,
            "overall_status": status,
            "enrollment": row.get("enrollment", ""),
            "registry_title": row.get("registry_title", ""),
            "primary_outcomes": row.get("primary_outcomes", ""),
            "source_url": row.get("source_url", ""),
            "recommended_action": action,
        })
    queue.sort(key=lambda row: (row["review_priority"], row["trial_id"]))
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(queue[0].keys()) if queue else ["review_priority"])
        writer.writeheader()
        writer.writerows(queue)
    counts = {}
    for row in queue:
        counts[row["review_priority"]] = counts.get(row["review_priority"], 0) + 1
    print(json.dumps({"rows": len(queue), "priority_counts": counts, "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
