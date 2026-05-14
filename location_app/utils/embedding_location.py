"""
TF-IDF Embedding + Cosine Similarity based location prediction.

Thay thế hoàn toàn LLM (Gemini/OpenAI). Không cần API bên ngoài.

Pipeline:
  1. Khi khởi động: build TF-IDF index từ WorldCityDataset (thành phố dân số ≥ MIN_POPULATION)
  2. Khi predict: lọc keyword → embed → cosine similarity → top cities
  3. Kết quả snap về WorldCityDataset để lấy tọa độ chính xác
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .keyword_extractor import extract_keywords, keywords_to_query
from .world_city_dataset import WorldCityDataset

# Ngưỡng dân số tối thiểu để đưa vào TF-IDF index
# ~100K → khoảng 5,000–8,000 thành phố, đủ phủ toàn cầu, nhẹ và nhanh
MIN_POPULATION_FOR_INDEX = 100_000

# Số thành phố tối đa trong index (an toàn về RAM)
MAX_INDEX_SIZE = 10_000


def _normalize_text(text: str) -> str:
    """Fold unicode → ASCII, lowercase, giữ chữ cái và số."""
    folded = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    lowered = folded.lower()
    return re.sub(r"[^a-z0-9\s]+", " ", lowered).strip()


def _build_corpus_from_dataset(
    dataset: WorldCityDataset,
) -> tuple[list[int], list[str], list[str]]:
    """
    Xây dựng corpus TF-IDF từ WorldCityDataset.

    Chỉ lấy thành phố có population >= MIN_POPULATION_FOR_INDEX.
    Mỗi document = label thành phố (lặp để tăng trọng số).

    Returns:
        (indices_in_dataset, city_labels, documents)
    """
    indices: list[int] = []
    labels: list[str] = []
    documents: list[str] = []

    for i, row in enumerate(dataset.city_rows):
        population = int(row[8] or 0)  # CITY_POPULATION = 8
        if population < MIN_POPULATION_FOR_INDEX:
            continue

        label = str(row[1])          # CITY_LABEL = 1
        name = str(row[2])           # CITY_NAME = 2
        ascii_name = str(row[3])     # CITY_ASCII_NAME = 3
        country = str(row[4])        # CITY_COUNTRY = 4

        # Normalize label thành ASCII để TF-IDF hiểu
        norm_label = _normalize_text(label)
        norm_name = _normalize_text(name)
        norm_ascii = _normalize_text(ascii_name)
        norm_country = _normalize_text(country)

        # Document = tên (lặp 4 lần) + ascii_name + country — tăng trọng số tên thành phố
        doc = f"{norm_name} {norm_name} {norm_name} {norm_name} {norm_ascii} {norm_label} {norm_country}"

        indices.append(i)
        labels.append(label)
        documents.append(doc)

        if len(indices) >= MAX_INDEX_SIZE:
            break

    return indices, labels, documents


# ---------------------------------------------------------------------------
# Singleton index — lazy-init khi lần đầu được gọi
# ---------------------------------------------------------------------------

class _EmbeddingIndex:
    """TF-IDF index singleton — lazy build từ WorldCityDataset."""

    def __init__(self):
        self._built = False
        self._dataset_indices: list[int] = []
        self._city_labels: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._city_matrix = None

    def build(self, dataset: WorldCityDataset) -> None:
        """Build index từ dataset (gọi 1 lần)."""
        if self._built:
            return

        indices, labels, documents = _build_corpus_from_dataset(dataset)

        self._dataset_indices = indices
        self._city_labels = labels

        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),   # unigram + bigram (trigram gây noise với tên thành phố)
            min_df=1,
            sublinear_tf=True,
            max_features=50_000,  # giới hạn vocabulary
        )
        self._city_matrix = self._vectorizer.fit_transform(documents)
        self._built = True

    def query(
        self,
        text: str,
        dataset: WorldCityDataset,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Trả về top_k thành phố có cosine similarity cao nhất với `text`.
        Text sẽ được lọc keyword trước khi embed.
        """
        if not self._built:
            self.build(dataset)

        # Lọc keyword — bỏ noise, stopwords, URL, emoji
        keywords = extract_keywords(text)
        query_text = keywords_to_query(keywords) if keywords else _normalize_text(text)

        if not query_text.strip():
            return []

        query_vec = self._vectorizer.transform([query_text.lower()])
        sims = cosine_similarity(query_vec, self._city_matrix).flatten()

        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score < 0.01:
                break

            dataset_idx = self._dataset_indices[idx]
            lat = float(dataset.latitudes[dataset_idx])
            lng = float(dataset.longitudes[dataset_idx])

            results.append({
                "city": self._city_labels[idx],
                "score": round(score, 4),
                "lat": lat,
                "lng": lng,
            })
        return results

    @property
    def index_size(self) -> int:
        return len(self._city_labels)


# Module-level singleton — build lazy khi predict_location_by_similarity được gọi lần đầu
_index = _EmbeddingIndex()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_embedding_index(dataset: WorldCityDataset) -> None:
    """
    Pre-build index ngay khi server khởi động (gọi từ views.get_services).
    Nếu không gọi, index sẽ tự build lần đầu khi predict được gọi (cold start ~0.5s).
    """
    _index.build(dataset)


def predict_location_by_similarity(
    text: str,
    dataset: WorldCityDataset,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Dự đoán vị trí từ văn bản tự do bằng TF-IDF cosine similarity.

    Returns a dict suitable for JsonResponse (JSON-serializable).
    """
    if not _index._built:
        _index.build(dataset)

    candidates = _index.query(text, dataset, top_k=top_k)

    if not candidates:
        raise ValueError("Không tìm thấy thành phố phù hợp từ văn bản đã nhập.")

    best = candidates[0]
    city_name = best["city"]
    confidence = best["score"]
    lat = best["lat"]
    lng = best["lng"]

    # Snap về WorldCityDataset để lấy tọa độ chính xác hơn
    idx = dataset.resolve_bias_index(city_name)
    if idx is not None:
        resolved_label = dataset.get_city_label(idx)
        resolved_lat = float(dataset.latitudes[idx])
        resolved_lng = float(dataset.longitudes[idx])
        dataset_aligned = True
    else:
        resolved_label = city_name
        resolved_lat = lat
        resolved_lng = lng
        dataset_aligned = False

    predicted_city_point = {
        "city": resolved_label,
        "score": confidence,
        "lat": resolved_lat,
        "lng": resolved_lng,
    }

    return {
        "success": True,
        "source": "embedding",
        "predicted_city": resolved_label,
        "predicted_city_point": predicted_city_point,
        "confidence": confidence,
        "top_cities": candidates,
        "dataset_aligned": dataset_aligned,
        "rationale_vi": (
            f"TF-IDF Embedding similarity: văn bản có độ tương đồng cao nhất "
            f"với '{city_name}' (score={confidence:.3f}), "
            f"index gồm {_index.index_size:,} thành phố lớn toàn cầu."
        ),
    }
