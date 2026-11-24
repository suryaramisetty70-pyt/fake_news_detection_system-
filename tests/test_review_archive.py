import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from pathlib import Path
from tempfile import TemporaryDirectory
from utils.search_verifier import verify_claim_on_web
from utils.review_archive import archived_review, records


class ArchiveAndControlsTests(unittest.TestCase):
    def test_every_record_preserves_original_evidence_location(self):
        locations = []
        for claim, entries in records().items():
            review = archived_review(claim)
            self.assertEqual(len(review["matches"]), len(entries))
            locations.extend(line for _, line in entries)
        self.assertEqual(sorted(locations), list(range(1, 1536)))

    def test_archived_ratings_and_changed_claim(self):
        claim = "Global warming is driving polar bears toward extinction"
        with patch("requests.get", side_effect=AssertionError("Local lookup expected")):
            self.assertEqual(verify_claim_on_web(claim)["verdict"], "ARCHIVE SUPPORTED")
            self.assertEqual(verify_claim_on_web("The polar bear population has been growing.")["verdict"], "ARCHIVE REFUTED")
        self.assertIsNone(archived_review(claim + " today"))
        for label in ("DISPUTED", "NOT_ENOUGH_INFO"):
            example = next(k for k, rows in records().items() if rows[0][0] == label)
            self.assertIsNone(archived_review(example)["verdict"])

    def test_example_submit_and_clear(self):
        with TemporaryDirectory() as folder, patch("database.db_handler.DB_PATH", Path(folder) / "test.db"):
            page = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
            for example, verdict in (("try_fake", "CONTRADICTED BY SOURCE"), ("try_real", "VERIFIED REAL NEWS"),
                                     ("try_archive", "SUPPORTED IN 2020 REVIEW")):
                page.button(key=example).click().run()
                page.button(key="check_text").click().run()
                self.assertFalse(page.exception)
                self.assertTrue(any(verdict in node.value for node in page.markdown))
            page.button(key="clear_text").click().run()
            self.assertEqual(page.text_area(key="text_input_area").value, "")
