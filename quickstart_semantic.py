#!/usr/bin/env python
"""
Quick start guide for Semantic Embeddings + Geo Database.

Run this after setting up the project to verify everything works.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tweet_locator.settings')
django.setup()

from location_app.utils.world_city_dataset import WorldCityDataset
from location_app.utils.semantic_inference import infer_location_semantic, clear_cache
from location_app.models import LocationQuery, SemanticLocation


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_dataset_loading():
    print_section("1. Testing Dataset Loading")
    
    try:
        dataset = WorldCityDataset()
        print(f"✓ Loaded {dataset.total_cities} cities")
        print(f"  Sample cities: {dataset.city_rows[0]}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_semantic_inference():
    print_section("2. Testing Semantic Inference")
    
    try:
        dataset = WorldCityDataset()
        
        test_queries = [
            "Big Ben is iconic",
            "Eiffel Tower view",
            "Times Square lights",
        ]
        
        for query in test_queries:
            results = infer_location_semantic(query, dataset, top_k=1)
            if results:
                top = results[0]
                print(f"✓ '{query}' → {top['city']} (confidence: {top['confidence']})")
            else:
                print(f"✗ '{query}' → No results")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    print_section("3. Testing Database Models")
    
    try:
        # Check tables exist
        semantic_count = SemanticLocation.objects.count()
        query_count = LocationQuery.objects.count()
        
        print(f"✓ SemanticLocation table: {semantic_count} rows")
        print(f"✓ LocationQuery table: {query_count} rows")
        
        if semantic_count > 0:
            sample = SemanticLocation.objects.first()
            print(f"\n  Sample semantic location:")
            print(f"    City: {sample.city_label}")
            print(f"    Population: {sample.population}")
            print(f"    Landmarks: {sample.landmarks[:3]}")
            print(f"    Coverage Score: {sample.coverage_score:.3f}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_logging():
    print_section("4. Testing Query Logging")
    
    try:
        # Create a test query log
        LocationQuery.objects.create(
            query_text="Test query for semantic inference",
            inferred_city="London",
            inferred_lat=51.51,
            inferred_lon=-0.13,
            confidence=0.95,
            method="semantic",
            keywords_extracted=["Big Ben", "Tower Bridge"]
        )
        
        # Retrieve it
        latest = LocationQuery.objects.latest('created_at')
        print(f"✓ Query logged: {latest.query_text}")
        print(f"  Result: {latest.inferred_city} (confidence: {latest.confidence})")
        print(f"  Method: {latest.method}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_next_steps():
    print_section("Next Steps")
    
    print("""
1. BUILD SEMANTIC INDEX (if not already done):
   python manage.py build_semantic_index
   
2. TEST API ENDPOINT:
   python manage.py runserver
   # Then POST to http://localhost:8000/predict_location/
   # with body: {"tweet": "Big Ben is amazing"}
   
3. ANALYZE RESULTS:
   python manage.py shell
   >>> from location_app.models import LocationQuery
   >>> LocationQuery.objects.all().values('method').distinct()
   
4. READ DOCUMENTATION:
   cat SEMANTIC_EMBEDDINGS.md
   
5. TRY EXAMPLES:
   python _test_semantic.py
   """)


def main():
    print_section("Semantic Embeddings Quick Start")
    
    results = {
        "Dataset Loading": test_dataset_loading(),
        "Semantic Inference": test_semantic_inference(),
        "Database Models": test_database_models(),
        "Query Logging": test_query_logging(),
    }
    
    print_section("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All systems ready! Your semantic embeddings setup is working.")
        print_next_steps()
    else:
        print("\n✗ Some tests failed. Check errors above and retry.")
        sys.exit(1)


if __name__ == "__main__":
    main()
