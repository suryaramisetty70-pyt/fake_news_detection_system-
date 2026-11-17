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
