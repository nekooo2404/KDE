import json
from unittest.mock import Mock, patch

from django.test import TestCase


class LocationAppViewTests(TestCase):
    def test_index_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liên kết bài đăng")
        self.assertContains(response, "Dataset hiện tại có")
        self.assertContains(response, "cityBiasSuggestions")

    def test_predict_location_returns_prediction(self):
        response = self.client.post(
            "/api/predict/",
            data=json.dumps(
                {
                    "tweet": "Beautiful sunset at the beach in Miami tonight.",
                    "cityBias": "",
                }
            ),
            content_type="application/json",
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertIn("Miami", payload["predicted_city"])
        self.assertIn("beach", payload["terms"])
        self.assertGreater(payload["confidence"], 0)
        self.assertGreaterEqual(payload["total_cities"], 150000)
        self.assertTrue(payload["top_cities"])

    def test_predict_location_supports_worldwide_city_aliases(self):
        response = self.client.post(
            "/api/predict/",
            data=json.dumps(
                {
                    "tweet": "Sunrise near Marina Bay and the Merlion before walking Orchard Road.",
                    "cityBias": "",
                }
            ),
            content_type="application/json",
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertIn("Singapore", payload["predicted_city"])
        self.assertIn("marina bay", payload["terms"])
        self.assertIn("merlion", payload["terms"])

    def test_predict_location_rejects_unknown_bias(self):
        response = self.client.post(
            "/api/predict/",
            data=json.dumps(
                {
                    "tweet": "Quick stop in Tokyo before dinner.",
                    "cityBias": "This City Does Not Exist",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_city_search_returns_suggestions(self):
        response = self.client.get("/api/city-search/?q=sing")
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertTrue(any("Singapore" in suggestion for suggestion in payload["suggestions"]))

    def test_world_city_endpoint_returns_large_dataset(self):
        response = self.client.get("/api/world-cities/")
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(payload["total_cities"], 150000)
        self.assertTrue(payload["cities"])

    def test_predict_location_reports_missing_signals(self):
        response = self.client.post(
            "/api/predict/",
            data=json.dumps({"tweet": "Completely generic status update", "cityBias": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["terms_found"], 0)

    @patch("location_app.utils.twitter.urlopen")
    def test_resolve_tweet_url_returns_tweet_text(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "author_name": "Test Author",
                "author_url": "https://twitter.com/testauthor",
                "html": (
                    '<blockquote class="twitter-tweet"><p lang="en" dir="ltr">'
                    "Hello from Times Square tonight."
                    "</p>&mdash; Test Author</blockquote>"
                ),
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = self.client.post(
            "/api/resolve-tweet/",
            data=json.dumps({"tweetUrl": "https://x.com/testauthor/status/1234567890"}),
            content_type="application/json",
        )

        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["tweet_id"], "1234567890")
        self.assertEqual(payload["author_handle"], "@testauthor")
        self.assertIn("Times Square", payload["tweet_text"])

    def test_resolve_tweet_url_rejects_non_tweet_url(self):
        response = self.client.post(
            "/api/resolve-tweet/",
            data=json.dumps({"tweetUrl": "https://example.com/not-a-tweet"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
