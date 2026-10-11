"""Regression checks for registry stopping-reason candidate labels."""

from build_pilot_evidence_review import classify_reason


def main() -> None:
    assert classify_reason("Study canceled based on results of different study with similar hypothesis, investigational agent, & patient") == ("cross_study_decision", "stated", "high")
    assert classify_reason("Closure of long term follow up (LTFU) as no beneficial information gained from continuing LTFU.") == ("followup_closure", "stated", "high")
    assert classify_reason("The study was terminated due to lack of efficacy.") == ("endpoint_failure", "stated", "high")
    assert classify_reason("Per protocol, study was terminated due to low rate of randomized patients.") == ("lead_in_futility", "stated", "high")
    print("Pilot stopping-reason classifier: pass")


if __name__ == "__main__":
    main()
