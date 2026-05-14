"""
Semantic Embeddings + Geo Database for cultural/landmark → location inference.

Pipeline:
  1. Embedding stage: Encode cultural references, landmarks, queries với sentence-transformers
  2. Similarity search: Cosine similarity trên embeddings  
  3. Geo ranking: Rerank candidates bằng proximity + population
  4. Confidence calculation: Dựa vào similarity score + population density
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer

from .keyword_extractor import extract_keywords
from .world_city_dataset import WorldCityDataset


# Cache embedding model (lazy load)
_embedding_model: SentenceTransformer | None = None
_landmark_cache: dict[str, np.ndarray] | None = None


def _get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    """Lấy embedding model (singleton, lazy load)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def _load_landmark_embeddings(
    dataset: WorldCityDataset,
    model: SentenceTransformer,
) -> dict[str, np.ndarray]:
    """
    Load/encode semantic embeddings cho tất cả landmarks từ dataset.
    
    Returns: dict[city_label] = embedding (1D array, 384 dims)
    """
    global _landmark_cache
    if _landmark_cache is not None:
        return _landmark_cache

    embeddings_dict: dict[str, np.ndarray] = {}
    
    # Encode city names + cultural references
    for i, row in enumerate(dataset.city_rows):
        label = str(row[1])  # CITY_LABEL
        name = str(row[2])   # CITY_NAME
        country = str(row[4])  # CITY_COUNTRY
        ascii_name = str(row[3])  # CITY_ASCII_NAME
        
        # Combine context: city_name, country
        text = f"{name} {ascii_name} {country}"
        
        if label not in embeddings_dict:
            # Encode once per city
            embedding = model.encode(text, convert_to_numpy=True)
            embeddings_dict[label] = embedding
    
    _landmark_cache = embeddings_dict
    return embeddings_dict



def _geo_proximity_score(
    candidate_lat: float,
    candidate_lon: float,
    semantic_candidates: list[dict[str, Any]],
) -> float:
    """
    Tính proximity score cho một candidate dựa vào semantic candidates (vectorized).
    Nếu có cluster semantic candidates gần đó → cao, không thì thấp.
    """
    if not semantic_candidates:
        return 0.5
    
    # Vectorize haversine calculation using NumPy
    R = 6371  # Earth radius in km
    
    candidate_lat_rad = np.radians(candidate_lat)
    candidate_lon_rad = np.radians(candidate_lon)
    
    # Convert all candidates to arrays
    lats = np.array([c.get("lat", 0) for c in semantic_candidates], dtype=np.float32)
    lons = np.array([c.get("lon", 0) for c in semantic_candidates], dtype=np.float32)
    
    lat_rads = np.radians(lats)
    lon_rads = np.radians(lons)
    
    delta_lat = lat_rads - candidate_lat_rad
    delta_lon = lon_rads - candidate_lon_rad
    
    # Vectorized haversine
    a = (
        np.sin(delta_lat / 2) ** 2 +
        np.cos(candidate_lat_rad) * np.cos(lat_rads) * np.sin(delta_lon / 2) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    distances = R * c
    
    # Min distance determines proximity score
    min_dist = np.min(distances)
    proximity = max(0, 1 - (min_dist / 5000))  # Normalize: 0km=1.0, 5000km=0.0
    
    return proximity


def infer_location_semantic(
    query_text: str,
    dataset: WorldCityDataset,
    top_k: int = 5,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    keywords: list[str] | None = None,  # Accept pre-extracted keywords to avoid duplicate encoding
) -> list[dict[str, Any]]:
    """
    Suy ra vị trí từ văn bản tự do bằng semantic embeddings + geo database.
    
    Args:
        query_text: Văn bản query (có thể chứa landmarks, cultural references)
        dataset: WorldCityDataset instance
        top_k: Số candidates trả về
        model_name: Sentence-transformers model ID
        keywords: Pre-extracted keywords (if None, will extract from query_text)
    
    Returns:
        List of dicts with keys: 
        {city, lat, lon, confidence, semantic_score, geo_score, keywords_found}
    """
    # 1. Extract keywords (or use provided ones)
    if keywords is None:
        keywords = extract_keywords(query_text)
    
    if not keywords:
        return []
    
    # 2. Get embedding model
    model = _get_embedding_model(model_name)
    
    # 3. Load landmark embeddings
    landmark_embeddings = _load_landmark_embeddings(dataset, model)
    
    if not landmark_embeddings:
        return []
    
    # 4. Encode query (reuse from caller or encode keywords)
    keywords_text = " ".join(keywords)
    query_embedding = model.encode(keywords_text, convert_to_numpy=True)
    
    # 5. Compute cosine similarity for all landmarks
    similarities: dict[str, float] = {}
    
    for city_label, landmark_embedding in landmark_embeddings.items():
        # Cosine similarity: 1 = identical, 0 = orthogonal, -1 = opposite
        sim = 1 - cosine(query_embedding, landmark_embedding)
        similarities[city_label] = float(sim)
    
    # 6. Get top candidates by semantic similarity
    sorted_candidates = sorted(
        similarities.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k * 2]  # Lấy gấp đôi để có enough candidates cho geo-ranking
    
    results = []
    
    for city_label, semantic_score in sorted_candidates:
        # Fast O(1) lookup using reverse index instead of O(n) loop
        dataset_idx = dataset.city_label_to_index.get(city_label)
        
        if dataset_idx is None:
            continue
        
        lat = float(dataset.latitudes[dataset_idx])
        lon = float(dataset.longitudes[dataset_idx])
        population = int(dataset.city_rows[dataset_idx][8] or 0)
        
        # Population boost: lớn hơn → confidence cao hơn
        population_factor = min(1.0, np.log1p(population) / 13)  # log scale
        
        # Geo proximity (if we have multiple candidates)
        semantic_results = [{"lat": lat, "lon": lon} for _, _ in sorted_candidates]
        geo_score = _geo_proximity_score(lat, lon, semantic_results[:5])
        
        # Final confidence = semantic + geo + population factors
        confidence = (
            semantic_score * 0.6 +  # Semantic similarity (60% weight)
            geo_score * 0.2 +        # Geographic proximity (20% weight)
            population_factor * 0.2  # Population density (20% weight)
        )
        
        results.append({
            "city": city_label,
            "lat": lat,
            "lon": lon,
            "confidence": round(confidence, 3),
            "semantic_score": round(semantic_score, 3),
            "geo_score": round(geo_score, 3),
            "population": population,
            "keywords_found": keywords,
        })
    
    # 7. Sort by confidence and return top_k
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:top_k]


def batch_infer_locations(
    queries: list[str],
    dataset: WorldCityDataset,
    top_k: int = 3,
) -> list[list[dict[str, Any]]]:
    """
    Infer locations cho batch of queries efficiently.
    Reuse embedding model và landmark embeddings.
    """
    results = []
    
    model = _get_embedding_model()
    _ = _load_landmark_embeddings(dataset, model)  # Pre-load once
    
    for query in queries:
        result = infer_location_semantic(query, dataset, top_k=top_k, 
                                          model_name=model.get_sentence_embedding_dimension())
        results.append(result)
    
    return results


def clear_cache() -> None:
    """Clear cached embeddings (e.g., for testing or model updates)."""
    global _embedding_model, _landmark_cache
    _embedding_model = None
    _landmark_cache = None
