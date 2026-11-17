import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import requests

from utils.search_verifier import verify_claim_on_web


class VerificationEvidenceTests(unittest.TestCase):
    claim = "The city will close Central Station on Monday"

    def verify(self, *headlines):
        root = ET.Element("rss")
        channel = ET.SubElement(root, "channel")
        for headline, publisher, domain in headlines:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = f"{headline} - {publisher}"
            ET.SubElement(item, "link").text = f"https://{domain}/article"
            ET.SubElement(item, "source", url=f"https://{domain}").text = publisher
        with patch("requests.get", return_value=Mock(content=ET.tostring(root))):
            return verify_claim_on_web(self.claim)

    def test_direct_publisher_match(self):
        result = self.verify((self.claim, "Reuters", "reuters.com"))
        self.assertEqual(result["verdict"], "REAL")
        self.assertEqual(result["trusted_sources_count"], 1)

    def test_related_coverage_and_fact_checker_do_not_decide(self):
        result = self.verify(
            ("The city will not close Central Station on Monday", "Reuters", "reuters.com"),
            ("Fact check: Central Station rumours", "Snopes", "snopes.com"),
            (self.claim, "Untrusted", "reuters.com.example.org"),
        )
        self.assertIsNone(result["verdict"])
        self.assertEqual([match["stance"] for match in result["matches"]], ["RELATED", "RELATED"])

    def test_explicit_fact_check_rating(self):
        result = self.verify((f'Fact check: "{self.claim}" — false', "Snopes", "snopes.com"))
        self.assertEqual(result["verdict"], "FAKE")

    def test_conflicting_evidence(self):
        result = self.verify(
            (self.claim, "Reuters", "reuters.com"),
            (f'"{self.claim}": False', "Snopes", "snopes.com"),
        )
        self.assertIsNone(result["verdict"])

    def test_provider_outage(self):
        with patch("requests.get", side_effect=requests.Timeout):
            result = verify_claim_on_web(self.claim)
        self.assertTrue(result["search_failed"])
        self.assertIsNone(result["verdict"])


class ReviewerClaimTests(unittest.TestCase):
    def test_private_home_claim_requires_identifiable_event(self):
        for claim in (
            "Modi is comming to his home",
            "Modi is coming to my home tomorrow",
            "Modi will visit her house",
        ):
            with self.subTest(claim=claim), patch("requests.get") as fetch:
                result = verify_claim_on_web(claim)
                self.assertIsNone(result["verdict"])
                self.assertIn("private-home", result["message"])
                fetch.assert_not_called()

    def test_current_office_claim_uses_official_record(self):
        from datetime import datetime, timezone

        from utils.official_records import check_current_office

        now = datetime(2026, 11, 17, tzinfo=timezone.utc)
        with patch("utils.official_records._fetch_tamil_nadu_holder", return_value="C. Joseph Vijay"):
            result = check_current_office("modi is the cm of tamil nadu", now)
            self.assertEqual(result["verdict"], "FAKE")
            self.assertEqual(result["matches"][0]["domain"], "tn.gov.in")
            self.assertEqual(check_current_office("Vijay is the CM of Tamil Nadu", now)["verdict"], "REAL")
            self.assertIsNone(check_current_office("Modi was the CM of Tamil Nadu", now))
            self.assertIsNone(check_current_office("Modi is the CM of Tamil Nadu?", now))
            self.assertIsNone(check_current_office("Modi is not the CM of Tamil Nadu", now))

    def test_snapshot_expires_and_newer_live_record_takes_priority(self):
        from datetime import datetime, timezone

        from utils.official_records import check_current_office

        claim = "Modi is the CM of Tamil Nadu"
        with patch("utils.official_records._fetch_tamil_nadu_holder", return_value=None):
            self.assertEqual(check_current_office(claim, datetime(2026, 11, 17, tzinfo=timezone.utc))["verdict"], "FAKE")
            self.assertIsNone(check_current_office(claim, datetime(2027, 1, 1, tzinfo=timezone.utc)))
        with patch("utils.official_records._fetch_tamil_nadu_holder", return_value="Narendra Modi"):
            self.assertEqual(check_current_office(claim, datetime(2026, 11, 17, tzinfo=timezone.utc))["verdict"], "REAL")

    def test_extracts_current_holder_from_official_page(self):
        from utils.official_records import _fetch_tamil_nadu_holder

        response = Mock(content=(
            "<div><h2>Honorable Chief Minister</h2><img src='portrait.png'>"
            "<h3>Thiru C. Joseph Vijay</h3><p>Chief Minister of Tamil Nadu</p></div>"
        ))
        with patch("requests.get", return_value=response):
            self.assertEqual(_fetch_tamil_nadu_holder(0), "C. Joseph Vijay")
