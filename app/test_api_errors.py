"""v1.0.69: a wrong API endpoint says so instead of dumping a web page.

The user's real failure: the saved endpoint was `https://aiplatform.googleapis.com` (no path), the app posts
`<endpoint>/chat/completions`, Google answered with an HTML "404 Not Found" page, and the Key test / chat showed
400 characters of `<!DOCTYPE html>`. JSON error bodies (the useful Google / xAI ones) must still pass through untouched.
"""

from __future__ import annotations

import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import genius_client  # noqa: E402

HTML_404 = "<!DOCTYPE html>\n<html lang=en>\n  <meta charset=utf-8>\n  <title>Error 404 (Not Found)!!1</title>"
GOOGLE_JSON = '[{"error": {"code": 404, "message": "models/3.6-flash is not found for API version v1main", "status": "NOT_FOUND"}}]'


def http_error(code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://x/y", code, "err", {}, io.BytesIO(body.encode("utf-8")))


class ApiError(unittest.TestCase):
    def test_a_web_page_becomes_one_readable_sentence_naming_the_address(self):
        msg = str(genius_client._api_error(404, HTML_404, "https://aiplatform.googleapis.com/chat/completions"))
        self.assertIn("API 404 from https://aiplatform.googleapis.com/chat/completions", msg)
        self.assertIn("web page", msg)
        self.assertIn("Model & endpoint", msg)
        self.assertNotIn("<", msg)
        self.assertLess(len(msg), 300)

    def test_a_web_page_is_caught_whatever_the_status_and_case(self):
        for code in (400, 403, 404, 502):
            with self.subTest(code=code):
                self.assertIn("web page", str(genius_client._api_error(code, "<HTML><body>oops", "u")))

    def test_an_empty_404_or_405_points_at_the_address(self):
        for code in (404, 405):
            with self.subTest(code=code):
                msg = str(genius_client._api_error(code, "", "https://h/x"))
                self.assertIn("no details", msg)
                self.assertIn("endpoint address", msg)

    def test_an_empty_body_on_other_statuses_does_not_blame_the_address(self):
        msg = str(genius_client._api_error(500, "", "https://h/x"))
        self.assertEqual(msg, "API 500: ")

    def test_json_error_bodies_pass_through_exactly_as_before(self):
        self.assertEqual(str(genius_client._api_error(404, GOOGLE_JSON, "u")), "API 404: " + GOOGLE_JSON)
        long_json = '{"error": "' + "x" * 600 + '"}'
        self.assertEqual(str(genius_client._api_error(400, long_json, "u")), "API 400: " + long_json[:400])


class ThroughTheRealCallers(unittest.TestCase):
    def test_post_json_reports_the_address_that_was_asked(self):
        with mock.patch.object(genius_client.urllib.request, "urlopen", side_effect=http_error(404, HTML_404)):
            with self.assertRaises(RuntimeError) as cm:
                genius_client._post_json("https://aiplatform.googleapis.com/chat/completions", "k", {"model": "m"})
        self.assertIn("https://aiplatform.googleapis.com/chat/completions", str(cm.exception))
        self.assertIn("web page", str(cm.exception))

    def test_post_json_keeps_a_json_error_verbatim(self):
        with mock.patch.object(genius_client.urllib.request, "urlopen", side_effect=http_error(404, GOOGLE_JSON)):
            with self.assertRaises(RuntimeError) as cm:
                genius_client._post_json("https://x/chat/completions", "k", {"model": "m"})
        self.assertEqual(str(cm.exception), "API 404: " + GOOGLE_JSON)

    def test_the_key_test_uses_the_same_wording(self):
        cfg = {"api_key": "k", "api_base": "https://aiplatform.googleapis.com", "model": "gemini-3.6-flash", "provider": "gemini"}
        with mock.patch.object(genius_client.urllib.request, "urlopen", side_effect=http_error(404, HTML_404)):
            with self.assertRaises(RuntimeError) as cm:
                genius_client.test_key(cfg)
        self.assertIn("https://aiplatform.googleapis.com/chat/completions", str(cm.exception))
        self.assertNotIn("<!DOCTYPE", str(cm.exception))


GOOGLE_503 = ('[{"error": {"code": 503, "message": "This model is currently experiencing high demand. Spikes in demand '
              'are usually temporary. Please try again later.", "status": "UNAVAILABLE"}}]')
GOOGLE_429 = '[{"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota).", "status": "RESOURCE_EXHAUSTED"}}]'


class BusyAndLimited(unittest.TestCase):
    """v1.7.0: 503 (overloaded) and 429 (usage limit) are one short plain sentence, not the JSON dump.
    The user's real case: gemini-3.8-flash answered 503 on one key while working on another."""

    def test_503_is_short_names_the_model_and_says_the_key_is_fine(self):
        msg = str(genius_client._api_error(503, GOOGLE_503, "u", "gemini-3.8-flash"))
        self.assertTrue(msg.startswith("gemini-3.8-flash is overloaded"))
        self.assertIn("Your key is fine", msg)
        self.assertIn("pick another key/model", msg)
        self.assertNotIn("{", msg)
        self.assertLess(len(msg), 200)

    def test_429_is_short_and_names_the_model(self):
        msg = str(genius_client._api_error(429, GOOGLE_429, "u", "gemini-3.6-flash"))
        self.assertIn("usage limit for gemini-3.6-flash", msg)
        self.assertNotIn("{", msg)

    def test_without_a_model_name_the_sentence_still_reads(self):
        self.assertTrue(str(genius_client._api_error(503, "", "u")).startswith("This model is overloaded"))
        self.assertIn("usage limit.", str(genius_client._api_error(429, "", "u")))

    def test_post_json_and_the_stream_pass_the_model(self):
        with mock.patch.object(genius_client.urllib.request, "urlopen", side_effect=http_error(503, GOOGLE_503)):
            with self.assertRaises(RuntimeError) as cm:
                genius_client._post_json("https://x/chat/completions", "k", {"model": "gemini-3.8-flash"})
        self.assertTrue(str(cm.exception).startswith("gemini-3.8-flash is overloaded"))
        with mock.patch.object(genius_client.urllib.request, "urlopen", side_effect=http_error(429, GOOGLE_429)):
            with self.assertRaises(RuntimeError) as cm:
                genius_client._stream_round("https://x/chat/completions", "k", {"model": "gemini-3.6-flash", "messages": []})
        self.assertIn("usage limit for gemini-3.6-flash", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
