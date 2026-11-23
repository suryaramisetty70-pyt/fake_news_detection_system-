import io
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from main import app


class ApplicationFlows(unittest.TestCase):
    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch("database.db_handler.DB_PATH", Path(folder) / "test.db"))
        self.enterContext(patch("utils.official_records._fetch_tamil_nadu_holder", return_value="C. Joseph Vijay"))
        self.client = self.enterContext(TestClient(app))
        self.claim = "Modi is the CM of Tamil Nadu"

    def test_text_history_and_analytics(self):
        for path in ("/", "/docs", "/api/health", "/api/scrapers/sources"):
            self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.post("/api/verify", json={"text": self.claim})
        self.assertEqual(response.json()["label"], "FAKE")
        self.assertEqual(self.client.get("/api/history").json()["history"][0]["prediction_label"], "FAKE")
        self.assertEqual(self.client.get("/api/analytics").json()["fake"], 1)
        self.assertEqual(self.client.post("/api/verify", json={"text": " "}).status_code, 400)

    def test_publication_and_altered_claim(self):
        feed = b'<rss><channel><item><title>Station closes in 2026 - Reuters</title><link>https://reuters.com/a</link><source url="https://reuters.com">Reuters</source></item></channel></rss>'
        with patch("requests.get", return_value=Mock(content=feed)):
            for text, label in (("Station closes in 2026", "REPORTED"),
                                ("Station closes in 2025", "UNABLE TO VERIFY"),
                                ("False: Station closes in 2026", "UNABLE TO VERIFY")):
                self.assertEqual(self.client.post("/api/verify", json={"text": text}).json()["label"], label)

    def test_voice_upload(self):
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setparams((1, 2, 16000, 0, "NONE", ""))
            wav.writeframes(bytes(32000))
        with patch("speech_recognition.Recognizer.recognize_google", return_value=self.claim):
            result = self.client.post("/api/voice-verify", files={"file": ("test.wav", audio.getvalue())})
        self.assertEqual(result.json()["prediction"]["label"], "FAKE")
        self.assertEqual(result.json()["transcription"], self.claim)

    def test_english_ocr(self):
        import shutil
        if not shutil.which("tesseract"):
            self.skipTest("English Tesseract installation required")
        image = Image.new("RGB", (850, 100), "white")
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
        ImageDraw.Draw(image).text((20, 20), self.claim, fill="black", font=font)
        data = io.BytesIO()
        image.save(data, format="PNG")
        response = self.client.post("/api/ocr-verify", files={"file": ("claim.png", data.getvalue())})
        self.assertEqual(response.json()["prediction"]["label"], "FAKE")
        self.assertEqual(response.json()["extracted_text"], self.claim)
