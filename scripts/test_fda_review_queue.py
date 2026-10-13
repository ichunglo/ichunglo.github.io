"""Unit checks for conservative FDA application candidate matching."""

import csv
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_fda_review_queue import build_queue, efficacy_candidates, normalized


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def tsv(rows: list[dict[str, str]]) -> bytes:
    import io

    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("cp1252")


class FdaReviewQueueTests(unittest.TestCase):
    def test_normalization(self) -> None:
        self.assertEqual(normalized("Lecanemab (Leqembi)"), "lecanemab")
        self.assertEqual(normalized("LECANEMAB-IRMB"), "lecanemab irmb")

    def test_candidates_are_not_marked_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            drugs = folder / "drugs.csv"
            curated = folder / "curated.csv"
            decisions = folder / "decisions.csv"
            archive = folder / "fda.zip"
            write_csv(drugs, [
                {"drug_id": "DRG-a", "generic_name": "alpha"},
                {"drug_id": "DRG-b", "generic_name": "beta"},
                {"drug_id": "DRG-c", "generic_name": "gamma"},
                {"drug_id": "DRG-d", "generic_name": "delta"},
            ])
            write_csv(curated, [{"drug_id": "DRG-a"}])
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("Applications.txt", tsv([
                    {"ApplNo": "000001", "ApplType": "NDA"},
                    {"ApplNo": "000002", "ApplType": "BLA"},
                    {"ApplNo": "000003", "ApplType": "ANDA"},
                    {"ApplNo": "000004", "ApplType": "NDA"},
                ]))
                handle.writestr("Products.txt", tsv([
                    {"ApplNo": "000001", "DrugName": "ALPHA", "ActiveIngredient": "ALPHA"},
                    {"ApplNo": "000002", "DrugName": "BETA", "ActiveIngredient": "BETA-XYZ"},
                    {"ApplNo": "000003", "DrugName": "GAMMA", "ActiveIngredient": "GAMMA"},
                    {"ApplNo": "000004", "DrugName": "BRAND-DELTA", "ActiveIngredient": "DELTA HYDROCHLORIDE"},
                ]))
                handle.writestr("Submissions.txt", tsv([
                    {"ApplNo": "000001", "SubmissionType": "ORIG", "SubmissionNo": "1", "SubmissionStatus": "AP", "SubmissionStatusDate": "2020-01-01 00:00:00", "SubmissionClassCodeID": "7"},
                    {"ApplNo": "000002", "SubmissionType": "ORIG", "SubmissionStatus": "AP", "SubmissionStatusDate": "2021-01-01 00:00:00"},
                    {"ApplNo": "000003", "SubmissionType": "ORIG", "SubmissionStatus": "AP", "SubmissionStatusDate": "2022-01-01 00:00:00"},
                    {"ApplNo": "000004", "SubmissionType": "ORIG", "SubmissionStatus": "AP", "SubmissionStatusDate": "2023-01-01 00:00:00"},
                    {"ApplNo": "000001", "SubmissionType": "SUPPL", "SubmissionNo": "2", "SubmissionStatus": "AP", "SubmissionStatusDate": "2024-01-01 00:00:00", "SubmissionClassCodeID": "2"},
                ]))
                handle.writestr("ApplicationDocs.txt", tsv([
                    {"ApplicationDocsTypeID": "2", "ApplNo": "000001", "SubmissionType": "ORIG", "SubmissionNo": "1", "ApplicationDocsURL": "http://www.accessdata.fda.gov/label-old.pdf", "ApplicationDocsDate": "2020-01-01 00:00:00"},
                    {"ApplicationDocsTypeID": "2", "ApplNo": "000001", "ApplicationDocsURL": "https://www.accessdata.fda.gov/label-new.pdf", "ApplicationDocsDate": "2022-01-01 00:00:00"},
                    {"ApplicationDocsTypeID": "2", "ApplNo": "000002", "ApplicationDocsURL": "https://untrusted.example/label.pdf", "ApplicationDocsDate": "2021-01-01 00:00:00"},
                    {"ApplicationDocsTypeID": "1", "ApplNo": "000001", "SubmissionType": "SUPPL", "SubmissionNo": "2", "ApplicationDocsURL": "https://www.accessdata.fda.gov/supplement-letter.pdf", "ApplicationDocsDate": "2024-01-01 00:00:00"},
                ]))
            rows, summary = build_queue(archive, "2026-10-09", drugs, curated, decisions)
            by_id = {row["drug_id"]: row for row in rows}
            self.assertEqual(by_id["DRG-a"]["candidate_match_basis"], "exact_active_ingredient")
            self.assertEqual(by_id["DRG-b"]["candidate_match_basis"], "exact_product_name")
            self.assertEqual(by_id["DRG-c"]["candidate_match_basis"], "no_exact_match")
            self.assertEqual(by_id["DRG-d"]["candidate_match_basis"], "ingredient_prefix_candidate")
            self.assertEqual(by_id["DRG-a"]["completeness_review_status"], "needs_full_indication_audit")
            self.assertEqual(by_id["DRG-a"]["candidate_latest_label_urls"], "https://www.accessdata.fda.gov/label-new.pdf")
            self.assertEqual(by_id["DRG-b"]["candidate_latest_label_urls"], "")
            self.assertEqual(summary["drugs_with_completed_indication_audit"], 0)
            write_csv(decisions, [{"drug_id": "DRG-a", "review_status": "verified_complete"}])
            reviewed, reviewed_summary = build_queue(archive, "2026-10-09", drugs, curated, decisions)
            self.assertEqual(reviewed[0]["completeness_review_status"], "verified_complete")
            self.assertEqual(reviewed_summary["drugs_with_completed_indication_audit"], 1)
            efficacy = efficacy_candidates(archive, rows)
            self.assertEqual(len(efficacy), 1)
            self.assertEqual(efficacy[0]["fda_approved_submission_date"], "2024-01-01")
            self.assertEqual(efficacy[0]["review_status"], "candidate_not_indication_verified")


if __name__ == "__main__":
    unittest.main()
