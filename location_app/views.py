import json

import hashlib
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import LocationQuery
from .tasks import log_location_query  # Async task
from .utils.embedding_location import build_embedding_index, predict_location_by_similarity
from .utils.semantic_inference import infer_location_semantic
from .utils.faiss_inference import infer_location_faiss, build_faiss_index_at_startup  # FAISS
from .utils.kde import LocalityKDE
from .utils.keyword_extractor import extract_keywords
from .utils.term_processor import TweetTermProcessor
from .utils.twitter import InvalidTweetUrlError, TweetResolutionError, TweetResolver
from .utils.world_city_dataset import WorldCityDataset

world_city_dataset = None
processor = None
kde = None
tweet_resolver = TweetResolver()


def _log_query_async(
    query_text: str,
    inferred_city: str | None,
    lat: float | None,
    lon: float | None,
    confidence: float | None,
    method: str = "semantic",
    keywords: list[str] | None = None,
) -> None:
    """Log location query directly to DB (synchronous fallback)."""
    try:
        LocationQuery.objects.create(
            query_text=query_text,
            inferred_city=inferred_city,
            inferred_lat=lat,
            inferred_lon=lon,
            confidence=confidence,
            method=method,
            keywords_extracted=keywords or [],
        )
    except Exception:
        # Don't fail the entire prediction if logging fails
        pass



def _prediction_payload_from_embedding(
    dataset,
    emb_result: dict,
    text_preview: str,
    city_bias: str,
) -> dict:
    """Đóng gói kết quả embedding để frontend tương thích với format cũ."""
    city = emb_result["predicted_city"]
    point = emb_result["predicted_city_point"]
    confidence = float(emb_result["confidence"])
    top_cities = emb_result.get("top_cities") or [point]

    return {
        "success": True,
        "predicted_city": city,
        "predicted_city_point": point,
        "confidence": confidence,
        "terms_found": 0,
        "terms": [],
        "city_scores": {c["city"]: c["score"] for c in top_cities},
        "top_cities": top_cities,
        "total_cities": dataset.total_cities,
        "tweet_preview": text_preview[:280],
        "city_bias": city_bias,
        "prediction_source": "semantic",
        "embedding": {
            "rationale_vi": emb_result.get("rationale_vi", ""),
            "dataset_aligned": emb_result.get("dataset_aligned", False),
        },
    }


def _prediction_payload_from_semantic(
    dataset,
    semantic_results: list[dict],
    text_preview: str,
    city_bias: str,
    keywords: list[str],
) -> dict:
    """Convert semantic inference results to frontend format."""
    if not semantic_results:
        return {
            "success": False,
            "error": "Không tìm thấy vị trí phù hợp"
        }
    
    top_result = semantic_results[0]
    city = top_result["city"]
    confidence = top_result.get("confidence", 0)
    
    return {
        "success": True,
        "predicted_city": city,
        "predicted_city_point": {
            "city": city,
            "lat": top_result.get("lat"),
            "lon": top_result.get("lon"),
            "score": confidence,
        },
        "confidence": confidence,
        "terms_found": len(keywords),
        "terms": keywords,
        "city_scores": {r["city"]: r.get("confidence", 0) for r in semantic_results},
        "top_cities": [
            {
                "city": r["city"],
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "score": r.get("confidence", 0),
            }
            for r in semantic_results
        ],
        "total_cities": dataset.total_cities,
        "tweet_preview": text_preview[:280],
        "city_bias": city_bias,
        "prediction_source": "semantic_embeddings",
        "semantic_details": {
            "semantic_score": top_result.get("semantic_score", 0),
            "geo_score": top_result.get("geo_score", 0),
            "population": top_result.get("population", 0),
        },
    }


def get_services():
    global world_city_dataset, processor, kde

    if world_city_dataset is None:
        world_city_dataset = WorldCityDataset()
        processor = TweetTermProcessor(world_city_dataset)
        kde = LocalityKDE(world_city_dataset)
        
        # Pre-build embedding index để tránh cold start
        build_embedding_index(world_city_dataset)
        
        # Pre-build FAISS index cho fast semantic search (1ms instead of 50ms!)
        build_faiss_index_at_startup(world_city_dataset)

    return world_city_dataset, processor, kde


@ensure_csrf_cookie
def index(request):
    """Main page"""
    dataset, _, _ = get_services()
    return render(
        request,
        "location_app/index.html",
        {
            "total_world_cities": dataset.total_cities,
            "city_dataset_source": dataset.source,
        },
    )


@csrf_exempt
@require_POST
def predict_location(request):
    """API endpoint for location prediction — KDE first, semantic embeddings fallback."""
    try:
        dataset, term_processor, locality_kde = get_services()
        data = json.loads(request.body or "{}")
        tweet = (data.get("tweet") or "").strip()
        raw_city_bias = (data.get("cityBias") or "").strip()

        if not tweet:
            return JsonResponse({"success": False, "error": "Vui long nhap noi dung tweet."}, status=400)

        # 1. Check Cache
        cache_key = f"predict_{hashlib.md5(tweet.encode('utf-8')).hexdigest()}_{hashlib.md5(raw_city_bias.encode('utf-8')).hexdigest()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse(cached_result)

        # 2. Resolve Bias
        city_bias = ""
        if raw_city_bias:
            city_bias_index = dataset.resolve_bias_index(raw_city_bias)
            if city_bias_index is None:
                return JsonResponse({"success": False, "error": "Khong tim thay thanh pho bias trong dataset toan cau."}, status=400)
            city_bias = dataset.get_city_label(city_bias_index)

        # 3. Prediction Pipeline
        def run_prediction_pipeline():
            # Step A: Extract Terms
            terms, term_locations = term_processor.extract_term_locations(tweet)
            keywords = extract_keywords(tweet)
            
            # Step B: Try KDE Model (Instant)
            predicted_city, confidence, city_scores, top_cities = locality_kde.predict_location(term_locations, city_bias=city_bias)
            if predicted_city:
                point = next((entry for entry in top_cities if entry["city"] == predicted_city), None)
                _log_query_async(tweet, predicted_city, point.get("lat") if point else None, point.get("lon") if point else None, confidence, method="kde", keywords=terms)
                return {
                    "success": True, "predicted_city": predicted_city, "predicted_city_point": point,
                    "confidence": float(confidence), "terms_found": len(terms), "terms": terms,
                    "city_scores": city_scores, "top_cities": top_cities, "total_cities": dataset.total_cities,
                    "tweet_preview": tweet[:280], "city_bias": city_bias, "prediction_source": "kde"
                }
            
            # Step C: Try TF-IDF Fallback (Super Fast, ~20ms)
            try:
                emb_result = predict_location_by_similarity(tweet, dataset)
                # Ensure the confidence score is acceptable before returning
                if emb_result.get("confidence", 0) > 0.05:
                    _log_query_async(tweet, emb_result.get("predicted_city"), emb_result.get("predicted_city_point", {}).get("lat"), emb_result.get("predicted_city_point", {}).get("lon"), emb_result.get("confidence"), method="tfidf", keywords=keywords)
                    return _prediction_payload_from_embedding(dataset, emb_result, tweet, city_bias)
            except Exception:
                pass
            
            # Step D: Try FAISS (Slow CPU, ~500ms)
            faiss_results = infer_location_faiss(tweet, dataset, top_k=5)
            if faiss_results:
                top = faiss_results[0]
                _log_query_async(tweet, top["city"], top.get("lat"), top.get("lon"), top.get("confidence"), method="faiss", keywords=keywords)
                return _prediction_payload_from_semantic(dataset, faiss_results, tweet, city_bias, keywords)
                
            # Step E: Full Semantic (Slowest fallback)
            semantic_results = infer_location_semantic(tweet, dataset, top_k=5, keywords=keywords)
            if semantic_results:
                top = semantic_results[0]
                _log_query_async(tweet, top["city"], top.get("lat"), top.get("lon"), top.get("confidence"), method="semantic", keywords=keywords)
                return _prediction_payload_from_semantic(dataset, semantic_results, tweet, city_bias, keywords)
                
            # Final fallback if all fails
            raise ValueError("Không thể định vị được thành phố từ nội dung văn bản này.")

        payload = run_prediction_pipeline()
        
        # Cache the successful payload for 24 hours
        if payload.get("success"):
            cache.set(cache_key, payload, timeout=86400)
            
        return JsonResponse(payload)

        # The above pipeline already returns JsonResponse properly.
        pass
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Payload JSON khong hop le."}, status=400)
    # Note: GlobalExceptionMiddleware will catch other unhandled exceptions


@csrf_exempt
@require_POST
def predict_location_batch(request):
    """
    Batch prediction using FAISS (5-10x faster than processing one-by-one).
    
    Request JSON:
    {
        "tweets": ["tweet1", "tweet2", ...],
        "cityBias": "optional"
    }
    
    Response: List of predictions, one per tweet
    """
    try:
        dataset, _, _ = get_services()
        data = json.loads(request.body or "{}")
        tweets = data.get("tweets", [])
        raw_city_bias = (data.get("cityBias") or "").strip()
        
        if not isinstance(tweets, list) or not tweets:
            return JsonResponse(
                {"success": False, "error": "tweets must be a non-empty array"},
                status=400,
            )
        
        # Resolve city bias if provided
        city_bias = ""
        if raw_city_bias:
            city_bias_index = dataset.resolve_bias_index(raw_city_bias)
            if city_bias_index is None:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Khong tim thay thanh pho bias trong dataset toan cau.",
                    },
                    status=400,
                )
            city_bias = dataset.get_city_label(city_bias_index)
        
        # Batch inference with FAISS
        from .utils.faiss_inference import batch_infer_locations_faiss
        
        batch_results = batch_infer_locations_faiss(
            queries=tweets,
            dataset=dataset,
            top_k=5,
        )
        
        # Format results
        predictions = []
        for tweet, results in zip(tweets, batch_results):
            if results:
                top = results[0]
                keywords = extract_keywords(tweet)
                
                # Log async
                _log_query_async(
                    tweet,
                    top["city"],
                    top.get("lat"),
                    top.get("lon"),
                    top.get("confidence"),
                    method="faiss_batch",
                    keywords=keywords,
                )
                
                predictions.append({
                    "tweet": tweet[:280],
                    "predicted_city": top["city"],
                    "predicted_city_point": {
                        "city": top["city"],
                        "lat": top["lat"],
                        "lon": top["lon"],
                        "score": top.get("confidence", 0),
                    },
                    "confidence": top.get("confidence", 0),
                    "search_method": "faiss",
                })
            else:
                predictions.append({
                    "tweet": tweet[:280],
                    "success": False,
                    "error": "Could not locate city",
                })
        
        return JsonResponse({
            "success": True,
            "count": len(predictions),
            "predictions": predictions,
            "total_cities": dataset.total_cities,
        })
    
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Payload JSON không hợp lệ."},
            status=400,
        )
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@require_GET
def search_cities(request):
    dataset, _, _ = get_services()
    query = (request.GET.get("q") or "").strip()
    suggestions = dataset.search(query, limit=12)
    return JsonResponse({"success": True, "suggestions": suggestions})


@require_GET
def world_city_points(request):
    dataset, _, _ = get_services()
    return HttpResponse(
        dataset.map_payload_json,
        content_type="application/json; charset=utf-8",
    )


@require_POST
def resolve_tweet_url(request):
    """Resolve a tweet URL into plain tweet text."""
    try:
        data = json.loads(request.body or "{}")
        tweet_url = (data.get("tweetUrl") or "").strip()
        if not tweet_url:
            return JsonResponse(
                {"success": False, "error": "Vui long nhap URL tweet."},
                status=400,
            )

        resolved_tweet = tweet_resolver.resolve(tweet_url)
        return JsonResponse({"success": True, **resolved_tweet})
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Payload JSON khong hop le."},
            status=400,
        )
    except InvalidTweetUrlError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)
    except TweetResolutionError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=502)


@require_POST
def extract_keywords_view(request):
    """Trả về danh sách keyword đã lọc từ nội dung tweet."""
    try:
        data = json.loads(request.body or "{}")
        text = (data.get("text") or data.get("tweet") or "").strip()
        keywords = extract_keywords(text) if text else []
        return JsonResponse({"success": True, "keywords": keywords})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Payload JSON không hợp lệ."}, status=400)
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
