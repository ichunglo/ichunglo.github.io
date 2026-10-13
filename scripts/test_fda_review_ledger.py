"""Guard against premature FDA full-coverage claims."""

import unittest

from build_fda_review_ledger import compile_ledger


class FdaReviewLedgerTests(unittest.TestCase):
    def test_rows_do_not_imply_review_completion(self) -> None:
        queue = [{
            "drug_id": "DRG-one", "generic_name": "one", "curated_indication_count": "1",
            "candidate_match_basis": "exact_active_ingredient", "candidate_applications": "NDA123456",
        }, {
            "drug_id": "DRG-two", "generic_name": "two", "curated_indication_count": "0",
            "candidate_match_basis": "no_exact_match", "candidate_applications": "",
        }]
        indications = [{"drug_id": "DRG-one", "application_number": "NDA123456"}]
        rows, summary = compile_ledger(queue, indications, [])
        self.assertEqual([row["review_status"] for row in rows], ["pending", "pending"])
        self.assertEqual(summary["pending"], 2)
        self.assertFalse(summary["all_drugs_reviewed"])

    def test_decision_requires_evidence_and_application(self) -> None:
        queue = [{
            "drug_id": "DRG-one", "generic_name": "one", "curated_indication_count": "1",
            "candidate_match_basis": "exact_active_ingredient", "candidate_applications": "NDA123456",
        }]
        indications = [{"drug_id": "DRG-one", "application_number": "NDA123456"}]
        decision = {
            "drug_id": "DRG-one", "review_status": "verified_complete", "reviewed_date": "2026-10-12",
            "applications_reviewed": "NDA123456",
            "supplement_review_note": "Only original approval found in FDA submission records",
            "source_urls": "https://www.fda.gov/a|https://www.accessdata.fda.gov/b",
            "review_note": "The original label has one indication and matches the approval notice.",
        }
        _, summary = compile_ledger(queue, indications, [decision])
        self.assertFalse(summary["all_drugs_reviewed"])
        self.assertEqual(summary["pending"], 0)
        self.assertEqual(summary["errors"], [])
        self.assertEqual(summary["verified_complete"], 1)
        decision["applications_reviewed"] = "NDA999999"
        _, invalid = compile_ledger(queue, indications, [decision])
        self.assertFalse(invalid["all_drugs_reviewed"])
        self.assertTrue(invalid["errors"])
        decision["applications_reviewed"] = "NDA123456"
        queue[0]["candidate_applications"] = "NDA123456|NDA654321"
        _, incomplete = compile_ledger(queue, indications, [decision])
        self.assertTrue(any("every candidate application" in error for error in incomplete["errors"]))


if __name__ == "__main__":
    unittest.main()
