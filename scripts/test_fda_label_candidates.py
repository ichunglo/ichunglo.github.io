"""Tests that openFDA label text remains unverified candidate data."""

import unittest

from build_fda_label_candidates import application_candidates, make_rows, select_label


class FdaLabelCandidateTests(unittest.TestCase):
    def test_latest_label_with_indication_is_selected(self) -> None:
        self.assertEqual(select_label([
            {"effective_time": "20250101", "indications_and_usage": ["one"]},
            {"effective_time": "20260101"},
            {"effective_time": "20251201", "indications_and_usage": ["two"]},
        ])["indications_and_usage"], ["two"])

    def test_candidate_status_and_exact_application_filter(self) -> None:
        queue = [{
            "drug_id": "DRG-a", "generic_name": "alpha",
            "candidate_match_basis": "ingredient_prefix_candidate",
            "candidate_applications": "NDA000001|BLA000002",
        }]
        self.assertEqual(set(application_candidates(queue)), {"NDA000001", "BLA000002"})
        payload = {"results": [{
            "effective_time": "20260101", "set_id": "abc",
            "openfda": {"application_number": ["NDA000001", "NDA999999"],
                        "generic_name": ["ALPHA SALT"], "brand_name": ["BRAND"]},
            "indications_and_usage": ["1 INDICATIONS AND USAGE alpha"],
        }]}
        rows = make_rows(queue, [(["NDA000001", "BLA000002"], payload, "https://api.fda.gov/query")])
        self.assertEqual(rows[0]["label_status"], "current_label_candidate")
        self.assertEqual(rows[0]["review_status"], "candidate_not_indication_verified")
        self.assertEqual(rows[1]["label_status"], "no_indication_text_found")
        self.assertEqual(rows[1]["indications_and_usage"], "")


if __name__ == "__main__":
    unittest.main()
