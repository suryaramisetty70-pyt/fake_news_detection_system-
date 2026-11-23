import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from database.db_handler import save_prediction


class StreamlitHistoryTests(unittest.TestCase):
    def test_legacy_history_and_new_verdict_render_together(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "database.db_handler.DB_PATH", Path(folder) / "history.db"
        ):
            claim = "Earth is the first planet from the Sun"
            save_prediction(claim, {"label": "REAL", "model_type": "fallback", "confidence": 0.99})
            page = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
            self.assertFalse(page.exception)
            row = page.dataframe[-1].value.iloc[0]
            self.assertIn("LEGACY RESULT", row["Verdict"])
            self.assertEqual(row["Confidence"], "—")
            page.text_area[0].input(claim)
            page.button(key="check_text").click().run(timeout=30)
            self.assertFalse(page.exception)
            self.assertTrue(any("CONTRADICTED BY SOURCE" in node.value for node in page.markdown))
