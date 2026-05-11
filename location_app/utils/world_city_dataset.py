import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
from django.conf import settings


CITY_ID = 0
CITY_LABEL = 1
CITY_NAME = 2
CITY_ASCII_NAME = 3
CITY_COUNTRY = 4
CITY_ADMIN1 = 5
CITY_LAT = 6
CITY_LNG = 7
CITY_POPULATION = 8

MAX_ALIAS_CANDIDATES = 8
MAX_ALIAS_WORDS = 5
STOP_ALIASES = {
    "city",
    "north",
    "south",
    "east",
    "west",
    "central",
    "town",
    "village",
}


def normalize_search_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    lowered = folded.lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def tokenize_search_text(value: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", normalize_search_text(value))


class WorldCityDataset:
    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or (
            Path(settings.BASE_DIR) / "location_app" / "data" / "world_cities.json"
        )
        payload = self._load_payload()
        self.source = payload.get("source", "Unknown")
        self.generated_at = payload.get("generated_at", "")
        self.city_rows: Sequence[List] = payload.get("cities", [])
        self.total_cities = len(self.city_rows)

        self.labels: List[str] = []
        self.normalized_labels: List[str] = []
        self.label_index: Dict[str, int] = {}
        self.alias_index: Dict[str, tuple[int, ...]] = {}
        self.map_points: List[List[float | int]] = []

        self.latitudes = np.zeros(self.total_cities, dtype=np.float32)
        self.longitudes = np.zeros(self.total_cities, dtype=np.float32)
        self.term_densities = np.zeros(self.total_cities, dtype=np.float32)

        alias_buckets: dict[str, list[int]] = defaultdict(list)

        for index, row in enumerate(self.city_rows):
            label = str(row[CITY_LABEL])
            lat = float(row[CITY_LAT])
            lng = float(row[CITY_LNG])
            population = int(row[CITY_POPULATION] or 0)

            self.labels.append(label)
            normalized_label = normalize_search_text(label)
            self.normalized_labels.append(normalized_label)
            self.label_index.setdefault(normalized_label, index)

            self.latitudes[index] = lat
            self.longitudes[index] = lng
            self.term_densities[index] = self._population_density(population)
            self.map_points.append([lat, lng, population])

            for alias in {str(row[CITY_NAME]), str(row[CITY_ASCII_NAME])}:
                normalized_alias = normalize_search_text(alias)
                if not self._is_searchable_alias(normalized_alias):
                    continue
                bucket = alias_buckets[normalized_alias]
                if len(bucket) < MAX_ALIAS_CANDIDATES:
                    bucket.append(index)

        self.alias_index = {alias: tuple(indices) for alias, indices in alias_buckets.items()}
        self.max_alias_words = min(
            max((len(alias.split()) for alias in self.alias_index), default=1),
            MAX_ALIAS_WORDS,
        )
        self.map_payload_json = json.dumps(
            {
                "success": True,
                "source": self.source,
                "total_cities": self.total_cities,
                "cities": self.map_points,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _load_payload(self) -> Dict:
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Missing world city dataset at {self.data_path}. "
                "Run manage.py build_world_city_dataset first."
            )

        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _is_searchable_alias(self, alias: str) -> bool:
        if not alias or alias in STOP_ALIASES:
            return False

        parts = alias.split()
        if len(parts) == 1:
            token = parts[0]
            if len(token) < 4 or token.isdigit():
                return False

        return True

    def _population_density(self, population: int) -> float:
        if population <= 0:
            return 0.58

        scaled = min(math.log10(population + 1) / 8.0, 0.34)
        return float(0.56 + scaled)

    def candidate_indices_for_alias(self, alias: str) -> tuple[int, ...]:
        return self.alias_index.get(normalize_search_text(alias), ())

    def resolve_bias_index(self, value: str) -> int | None:
        normalized_value = normalize_search_text(value)
        if not normalized_value:
            return None

        if normalized_value in self.label_index:
            return self.label_index[normalized_value]

        aliases = self.alias_index.get(normalized_value)
        if aliases:
            return aliases[0]

        return None

    def get_city_label(self, index: int) -> str:
        return self.labels[index]

    def get_city_score_entry(self, index: int, score: float) -> Dict[str, float | str]:
        return {
            "city": self.get_city_label(index),
            "score": float(score),
            "lat": float(self.latitudes[index]),
            "lng": float(self.longitudes[index]),
        }

    def build_term_locations(self, alias: str, city_indices: Sequence[int]) -> List[Dict]:
        locations = []
        for index in city_indices:
            locations.append(
                {
                    "term": alias,
                    "city": self.get_city_label(index),
                    "lat": float(self.latitudes[index]),
                    "lng": float(self.longitudes[index]),
                    "density": float(self.term_densities[index]),
                }
            )
        return locations

    def search(self, query: str, limit: int = 10) -> List[str]:
        normalized_query = normalize_search_text(query)
        if len(normalized_query) < 2:
            return []

        results = []
        seen = set()

        for index, normalized_label in enumerate(self.normalized_labels):
            if normalized_label.startswith(normalized_query):
                label = self.labels[index]
                if label not in seen:
                    results.append(label)
                    seen.add(label)
                    if len(results) >= limit:
                        return results

        for index, normalized_label in enumerate(self.normalized_labels):
            if normalized_query in normalized_label:
                label = self.labels[index]
                if label not in seen:
                    results.append(label)
                    seen.add(label)
                    if len(results) >= limit:
                        return results

        return results
