"""LLM-backed location guess from free-form keywords or short text."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .world_city_dataset import WorldCityDataset

USER_PROMPT_TEMPLATE = """Phân tích đoạn sau và suy ra địa điểm (thành phố) có khả năng nhất.
Chỉ trả về JSON đúng schema đã nói, không markdown.

Đoạn cần phân tích:
---
{keywords}
---
"""


def _ai_settings() -> tuple[str, str]:
    api_key = (getattr(settings, "GEMINI_API_KEY", None) or "").strip()
    model = (getattr(settings, "GEMINI_MODEL", None) or "gemini-2.0-flash").strip()
    return api_key, model


def is_ai_location_configured() -> bool:
    api_key, _ = _ai_settings()
    return bool(api_key)


def _parse_json_object(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise ValueError("Phản hồi AI rỗng.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("AI không trả về JSON hợp lệ.") from exc

    if not isinstance(data, dict):
        raise ValueError("AI phải trả về một object JSON.")

    return data


def _call_gemini_json(keywords: str, timeout: int = 45) -> dict[str, Any]:
    api_key, model = _ai_settings()
    if not api_key:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY trong settings hoặc biến môi trường.")

    system = (
        "You infer likely real-world locations from keywords or short text (any language). "
        "Return ONLY a JSON object with keys: "
        "city (string, English city name), country (string), latitude (number WGS84), "
        "longitude (number WGS84), confidence (0..1), keywords_spotted (array of strings), "
        "rationale_vi (Vietnamese, 1-2 sentences). "
        "If ambiguous, still pick one best city and lower confidence."
    )
    user = USER_PROMPT_TEMPLATE.format(keywords=keywords.strip() or "(empty)")

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Lỗi HTTP từ Gemini ({exc.code}): {detail[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Không kết nối được tới Gemini API: {exc}") from exc

    outer = json.loads(raw)
    candidates = outer.get("candidates") or []
    if not candidates:
        raise RuntimeError("Phản hồi Gemini không có candidates.")

    content_parts = candidates[0].get("content", {}).get("parts") or []
    if not content_parts:
        raise RuntimeError("Phản hồi Gemini không có nội dung.")

    content_text = content_parts[0].get("text") or ""
    return _parse_json_object(content_text)


def _snap_to_dataset(
    dataset: WorldCityDataset,
    city: str,
    lat: float,
    lng: float,
) -> tuple[int | None, str | None]:
    """Prefer dataset city label if we can resolve the AI city name."""
    if city.strip():
        idx = dataset.resolve_bias_index(city)
        if idx is not None:
            return idx, dataset.get_city_label(idx)

    # Fuzzy prefix / substring match on labels
    suggestions = dataset.search(city, limit=5)
    if suggestions:
        idx = dataset.resolve_bias_index(suggestions[0])
        if idx is not None:
            return idx, dataset.get_city_label(idx)

    # Nearest city by haversine-lite (small distances: Euclidean on lat/lng is enough for ranking)
    best_idx: int | None = None
    best_dist = float("inf")
    for i in range(dataset.total_cities):
        dlat = float(dataset.latitudes[i]) - lat
        dlng = float(dataset.longitudes[i]) - lng
        dist = dlat * dlat + dlng * dlng
        if dist < best_dist:
            best_dist = dist
            best_idx = i

    # Only snap if reasonably close (~2 degrees ~ 200km max)
    if best_idx is not None and best_dist ** 0.5 < 2.5:
        return best_idx, dataset.get_city_label(best_idx)

    return None, None


def predict_location_from_keywords(
    keywords: str,
    dataset: WorldCityDataset,
) -> dict[str, Any]:
    """
    Call LLM, validate fields, optionally align to world city dataset.

    Returns a dict suitable for JsonResponse (JSON-serializable).
    """
    raw = _call_gemini_json(keywords)

    city = str(raw.get("city") or "").strip()
    country = str(raw.get("country") or "").strip()
    try:
        latitude = float(raw["latitude"])
        longitude = float(raw["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("AI thiếu latitude/longitude hợp lệ.") from exc

    try:
        confidence = float(raw.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    keywords_spotted = raw.get("keywords_spotted") or []
    if not isinstance(keywords_spotted, list):
        keywords_spotted = []
    keywords_spotted = [str(x) for x in keywords_spotted if str(x).strip()]

    rationale_vi = str(raw.get("rationale_vi") or "").strip()

    idx, resolved_label = _snap_to_dataset(dataset, city, latitude, longitude)

    result: dict[str, Any] = {
        "success": True,
        "source": "ai",
        "ai_city": city,
        "ai_country": country,
        "ai_latitude": latitude,
        "ai_longitude": longitude,
        "ai_confidence": confidence,
        "keywords_spotted": keywords_spotted,
        "rationale_vi": rationale_vi,
    }

    if idx is not None and resolved_label:
        result["predicted_city"] = resolved_label
        result["predicted_city_point"] = {
            "city": resolved_label,
            "score": confidence,
            "lat": float(dataset.latitudes[idx]),
            "lng": float(dataset.longitudes[idx]),
        }
        result["dataset_aligned"] = True
    else:
        result["predicted_city"] = city or "Unknown"
        result["predicted_city_point"] = {
            "city": result["predicted_city"],
            "score": confidence,
            "lat": latitude,
            "lng": longitude,
        }
        result["dataset_aligned"] = False

    return result
