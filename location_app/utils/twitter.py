from __future__ import annotations

import re
import json
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from django.utils.html import strip_tags


class InvalidTweetUrlError(ValueError):
    """Raised when the submitted URL is not a valid tweet URL."""


class TweetResolutionError(RuntimeError):
    """Raised when tweet contents cannot be resolved from a valid URL."""


class TweetResolver:
    OEMBED_ENDPOINT = "https://publish.twitter.com/oembed"
    ALLOWED_HOSTS = {
        "twitter.com",
        "www.twitter.com",
        "mobile.twitter.com",
        "x.com",
        "www.x.com",
        "mobile.x.com",
    }
    STATUS_PATH_RE = re.compile(r"/(?P<user>[A-Za-z0-9_]+)/status/(?P<tweet_id>\d+)")

    def resolve(self, raw_url: str) -> dict:
        canonical_url, tweet_id = self._normalize_tweet_url(raw_url)
        payload = self._fetch_oembed_payload(canonical_url)
        text = self._extract_text(payload)

        if not text:
            raise TweetResolutionError("Khong the doc noi dung tweet tu URL nay.")

        return {
            "tweet_id": tweet_id,
            "tweet_url": canonical_url,
            "tweet_text": text,
            "author_name": payload.get("author_name", ""),
            "author_handle": self._extract_handle(payload.get("author_url", "")),
        }

    def _normalize_tweet_url(self, raw_url: str) -> tuple[str, str]:
        parsed = urlparse((raw_url or "").strip())

        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in self.ALLOWED_HOSTS:
            raise InvalidTweetUrlError("URL phai la link tweet hop le tu x.com hoac twitter.com.")

        match = self.STATUS_PATH_RE.search(parsed.path)
        if not match:
            raise InvalidTweetUrlError("URL can tro truc tiep den mot tweet cu the.")

        username = match.group("user")
        tweet_id = match.group("tweet_id")
        return f"https://twitter.com/{username}/status/{tweet_id}", tweet_id

    def _fetch_oembed_payload(self, canonical_url: str) -> dict:
        query = urlencode(
            {
                "url": canonical_url,
                "omit_script": "1",
                "hide_thread": "1",
                "dnt": "1",
            }
        )
        request = Request(
            f"{self.OEMBED_ENDPOINT}?{query}",
            headers={"User-Agent": "TweetLocator/1.0"},
        )

        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise TweetResolutionError(
                "Khong the ket noi toi dich vu doc tweet luc nay. Thu lai sau."
            ) from exc
        except json.JSONDecodeError as exc:
            raise TweetResolutionError("Dich vu tweet tra ve du lieu khong hop le.") from exc

    def _extract_text(self, payload: dict) -> str:
        html = payload.get("html", "")
        paragraph_match = re.search(r"<p[^>]*>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL)
        if not paragraph_match:
            return ""

        raw_text = strip_tags(paragraph_match.group(1))
        text = unescape(raw_text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_handle(self, author_url: str) -> str:
        parsed = urlparse(author_url or "")
        handle = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
        return f"@{handle}" if handle else ""
