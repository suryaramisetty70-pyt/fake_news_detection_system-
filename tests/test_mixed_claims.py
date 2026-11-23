"""Exercise the public verification endpoint with adversarial variations of claims."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient
from main import app


def rss(items):
    channel = ET.Element("channel")
    for title, domain in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title + " - Publisher"
        ET.SubElement(item, "source", url="https://" + domain).text = "Publisher"
        ET.SubElement(item, "link").text = "https://" + domain + "/article"
    root = ET.Element("rss")
    root.append(channel)
    return Mock(content=ET.tostring(root))


class MixedClaims(unittest.TestCase):
    def test_verdict_matrix(self):
        unverified = "UNABLE TO VERIFY"
        headline = "Chennai opens three libraries on Monday"
        rating = ("True: " + headline, "snopes.com")
        cases = [
            ("modi is the cm of tamilnadu", [], "FAKE"),
            ("Vijay is the CM of Tamil Nadu", [], "REAL"),
            ("modi is comming to my home", [], unverified),
            ("Modi will play cricket at my house tomorrow", [], unverified),
            ("All college exams are cancelled tomorrow", [], unverified),
            ("Flying elephants won the college hackathon", [], unverified),
            ("A dragon landed in Chennai and opened a bank", [], unverified),
            ("Earth is the third planet from the Sun", [], "REAL"),
            ("Earth is the first planet from the Sun", [], "FAKE"),
            ("Earth is not the third planet from the Sun", [], "FAKE"),
            ("Mercury is not the third planet from the Sun", [], "REAL"),
            ("Mars is a planet", [], "REAL"),
            ("Pluto is a planet", [], "FAKE"),
            ("Pluto is a dwarf planet", [], "REAL"),
            ("Venus is a dwarf planet", [], "FAKE"),
            ("Pluto was a planet in 1990", [], unverified),
            ("Pluto is a planet in my video game", [], unverified),
            ("Mars is a planet and Chennai is on Mars", [], unverified),
            ("Is Earth the first planet from the Sun?", [], unverified),
            (headline, [rating], "REAL"),
            (headline, [("False: " + headline, "factly.in")], "FAKE"),
            (headline, [rating, ("False: " + headline, "factly.in")], unverified),
            (headline, [(headline, "reuters.com")], "REPORTED"),
            (headline, [("True: " + headline + "?", "snopes.com")], unverified),
            (headline, [("Mostly true: " + headline, "snopes.com")], unverified),
            (headline, [("True: " + headline, "snopes.com.example.org")], unverified),
            (headline.replace("three", "thirty"), [rating], unverified),
            (headline.replace("Chennai", "Delhi"), [rating], unverified),
            (headline.replace("Monday", "Friday"), [rating], unverified),
            (headline.replace("opens", "closes"), [rating], unverified),
            ("Schools are closed tomorrow", [("True: Schools are closed tomorrow", "snopes.com")], unverified),
            ("రేపు అన్ని కాలేజీలకు సెలవు", [], unverified),
        ]
        with tempfile.TemporaryDirectory() as tmp, patch("database.db_handler.DB_PATH", Path(tmp)/"test.db"), \
             patch("utils.official_records._fetch_tamil_nadu_holder", return_value="C. Joseph Vijay"), TestClient(app) as client:
            for claim, feeds, expected in cases:
                with self.subTest(claim=claim, feeds=feeds), patch("requests.get", return_value=rss(feeds)):
                    response = client.post("/api/verify", json={"text": claim})
                    self.assertEqual(response.status_code, 200)
                    result = response.json()
                    self.assertEqual(result["label"], expected)
                    if expected in {"REAL", "FAKE"}:
                        self.assertTrue(any(m["stance"] == expected for m in result["web_check"]["matches"]))
