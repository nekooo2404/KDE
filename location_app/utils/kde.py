from typing import Dict, List, Tuple

import numpy as np

from .world_city_dataset import WorldCityDataset


class LocalityKDE:
    def __init__(
        self,
        world_city_dataset: WorldCityDataset | None = None,
        bandwidth: float = 0.65,
    ):
        self.world_city_dataset = world_city_dataset or WorldCityDataset()
        self.bandwidth = bandwidth
        self.total_cities = self.world_city_dataset.total_cities

    def gaussian_kernel(self, dist: np.ndarray) -> np.ndarray:
        return np.exp(-0.5 * (dist / self.bandwidth) ** 2)

    def compute_scores(self, points: List[Dict]) -> np.ndarray:
        scores = np.zeros(self.total_cities, dtype=np.float32)
        if not points:
            return scores

        for point in points:
            lat_delta = self.world_city_dataset.latitudes - point["lat"]
            lng_delta = self.world_city_dataset.longitudes - point["lng"]
            dist = np.sqrt((lat_delta ** 2) + (lng_delta ** 2))
            scores += point.get("density", 1.0) * self.gaussian_kernel(dist)

            canonical_city = point.get("canonical_city")
            if canonical_city:
                canonical_index = self.world_city_dataset.resolve_bias_index(canonical_city)
                if canonical_index is not None:
                    scores[canonical_index] += 0.12

        return scores / len(points)

    def predict_location(
        self,
        term_locations: List[Dict],
        city_bias: str = "",
        top_n: int = 20,
    ) -> Tuple[str | None, float, Dict[str, float], List[Dict]]:
        scores = self.compute_scores(term_locations)
        bias_index = self.world_city_dataset.resolve_bias_index(city_bias) if city_bias else None

        if bias_index is not None:
            scores[bias_index] += 0.2 if term_locations else 0.35

        if not term_locations and bias_index is None:
            return None, 0.0, {}, []

        best_index = int(np.argmax(scores))
        total_score = float(np.sum(scores))
        best_score = float(scores[best_index])
        confidence = best_score / total_score if total_score else 0.0

        top_count = min(top_n, self.total_cities)
        top_indices = np.argpartition(scores, -top_count)[-top_count:]
        ordered_top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        top_cities = [
            self.world_city_dataset.get_city_score_entry(int(index), float(scores[index]))
            for index in ordered_top_indices
            if float(scores[index]) > 0
        ]
        city_scores = {entry["city"]: float(entry["score"]) for entry in top_cities}

        return (
            self.world_city_dataset.get_city_label(best_index),
            float(confidence),
            city_scores,
            top_cities,
        )
