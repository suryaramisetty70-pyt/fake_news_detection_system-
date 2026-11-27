import unittest
from unittest.mock import Mock, patch

from utils.search_verifier import verify_claim_on_web


class PublisherReviewTests(unittest.TestCase):
    def check(self, text, rating="False"):
        claim = "The new bridge isn't open to bicycles."
        url = "https://www.factcheck.org/2024/04/bridge/"
        markup = f"""<div itemtype="https://schema.org/ClaimReview">
            <span itemprop="claimReviewed">{claim}</span>
            <div itemprop="reviewRating"><b itemprop="alternateName">{rating}</b></div>
            <span itemprop="datePublished">2024-04-12</span></div>"""

        def fetch(address, **kwargs):
            if "news.google.com" in address:
                return Mock(content=b"<rss><channel/></rss>")
            if "/wp-json/" in address:
                return Mock(json=lambda: [{"url": url}])
            self.assertEqual(address, url)
            return Mock(status_code=200, content=markup.encode())

        with patch("requests.get", side_effect=fetch):
            return verify_claim_on_web(text)

    def test_review_wins_with_citation(self):
        result = self.check("The new bridge is not open to bicycles")
        self.assertEqual(result["verdict"], "FAKE")
        self.assertIn("2024-04-12", result["matches"][0]["title"])

    def test_changed_statement_or_qualified_rating_abstains(self):
        for text in ("The new bridge is open to bicycles", "The old bridge isn't open to bicycles",
                     "The new bridge isn't open to bicycles today"):
            self.assertIsNone(self.check(text)["verdict"])
        self.assertIsNone(self.check("The new bridge isn't open to bicycles", "Mostly false")["verdict"])
