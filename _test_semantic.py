"""
Demonstration of Semantic Embeddings + Geo Database approach.

Usage:
  python _test_semantic.py

This script shows:
  1. Building semantic embeddings index
  2. Querying with cultural references/landmarks
  3. Comparing with TF-IDF approach
"""

import json
import time
from typing import Any

from location_app.utils.world_city_dataset import WorldCityDataset
from location_app.utils.semantic_inference import infer_location_semantic
from location_app.utils.embedding_location import predict_location_by_similarity


def print_result(method: str, result: list[dict[str, Any]]) -> None:
    """Pretty print inference results."""
    if not result:
        print(f"  {method}: No results\n")
        return
    
    print(f"\n  {method}:")
    for i, r in enumerate(result, 1):
        confidence = r.get("confidence", r.get("score", 0))
        print(
            f"    {i}. {r['city']} @ ({r.get('lat', 'N/A')}, {r.get('lon', 'N/A')}) "
            f"- confidence: {confidence}"
        )
        
        # Show semantic details if available
        if "semantic_score" in r:
            print(f"       semantic: {r['semantic_score']}, geo: {r.get('geo_score', 0)}")
        
        if "keywords_found" in r:
            print(f"       keywords: {r['keywords_found']}")


def main():
    print("=" * 70)
    print("Semantic Embeddings vs TF-IDF Location Inference")
    print("=" * 70)
    
    # Load dataset
    print("\nLoading world cities dataset...")
    dataset = WorldCityDataset()
    print(f"  ✓ Loaded {dataset.total_cities} cities")
    
    # Test queries: cultural/landmark references
    test_queries = [
        "Big Ben and Tower Bridge are beautiful, visited yesterday",
        "Eiffel Tower at sunset, magnifique!",
        "Mount Fuji views from Tokyo, cherry blossoms season",
        "Times Square is so bright at night",
        "Gondola ride in Venice, romantic atmosphere",
        "Great Wall hiking trip, exhausted but happy",
        "Statue of Liberty, American dream realized",
        "Taj Mahal sunset, absolutely breathtaking",
    ]
    
    print(f"\nTesting {len(test_queries)} queries...\n")
    
    for query in test_queries:
        print(f"Query: \"{query}\"")
        print("-" * 70)
        
        # Semantic embeddings (NEW APPROACH)
        start_time = time.time()
        try:
            semantic_result = infer_location_semantic(query, dataset, top_k=3)
            semantic_time = time.time() - start_time
            print_result(f"Semantic Embeddings ({semantic_time:.2f}s)", semantic_result)
        except Exception as e:
            print(f"  Semantic Embeddings Error: {e}")
        
        # TF-IDF (OLD APPROACH)
        start_time = time.time()
        try:
            tfidf_result = predict_location_by_similarity(query, dataset, top_k=3)
            tfidf_time = time.time() - start_time
            
            # Convert result format
            if isinstance(tfidf_result, dict) and "top_cities" in tfidf_result:
                tfidf_converted = tfidf_result["top_cities"]
            else:
                tfidf_converted = []
            
            print_result(f"TF-IDF Cosine ({tfidf_time:.2f}s)", tfidf_converted)
        except Exception as e:
            print(f"  TF-IDF Error: {e}")
        
        print()
    
    # Analysis
    print("\n" + "=" * 70)
    print("Key Differences:")
    print("=" * 70)
    print("""
    SEMANTIC EMBEDDINGS (NEW):
    ✓ Understands meaning: "Big Ben" → London, not lexical matching
    ✓ Multilingual support: works across languages
    ✓ Captures relationships: landmarks associated with cities
    ✓ Geo-aware: combines semantic + geographic proximity
    ✓ Slower first run (model download), then cached
    
    TF-IDF (OLD):
    ✗ Lexical only: requires exact keyword match
    ✗ Language-dependent: struggles with multilingual content
    ✗ No semantic understanding of landmarks
    ✓ Fast: already implemented, instant
    ✓ Lightweight: minimal dependencies
    
    RECOMMENDATION:
    - Use SEMANTIC for cultural/landmark references (better accuracy)
    - Fall back to TF-IDF for unknown landmarks or quick fallback
    """)
    
    print("=" * 70)


if __name__ == "__main__":
    main()
