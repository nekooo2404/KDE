import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .utils.kde import LocalityKDE
from .utils.term_processor import TweetTermProcessor
from .utils.twitter import InvalidTweetUrlError, TweetResolutionError, TweetResolver
from .utils.world_city_dataset import WorldCityDataset

world_city_dataset = None
processor = None
kde = None
tweet_resolver = TweetResolver()


def get_services():
    global world_city_dataset, processor, kde

    if world_city_dataset is None:
        world_city_dataset = WorldCityDataset()
        processor = TweetTermProcessor(world_city_dataset)
        kde = LocalityKDE(world_city_dataset)

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


@require_POST
def predict_location(request):
    """API endpoint for location prediction"""
    try:
        dataset, term_processor, locality_kde = get_services()
        data = json.loads(request.body or "{}")
        tweet = (data.get("tweet") or "").strip()
        raw_city_bias = (data.get("cityBias") or "").strip()

        if not tweet:
            return JsonResponse(
                {"success": False, "error": "Vui long nhap noi dung tweet."},
                status=400,
            )

        city_bias_index = None
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

        terms, term_locations = term_processor.extract_term_locations(tweet)
        predicted_city, confidence, city_scores, top_cities = locality_kde.predict_location(
            term_locations,
            city_bias=city_bias,
        )
        if predicted_city is None:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Khong tim thay term vi tri nao trong tweet nay.",
                    "terms_found": 0,
                    "terms": [],
                    "city_scores": {},
                    "top_cities": [],
                    "total_cities": dataset.total_cities,
                },
                status=422,
            )

        predicted_city_point = next(
            (entry for entry in top_cities if entry["city"] == predicted_city),
            None,
        )

        return JsonResponse(
            {
                "success": True,
                "predicted_city": predicted_city,
                "predicted_city_point": predicted_city_point,
                "confidence": float(confidence),
                "terms_found": len(terms),
                "terms": terms,
                "city_scores": city_scores,
                "top_cities": top_cities,
                "total_cities": dataset.total_cities,
                "tweet_preview": tweet[:280],
                "city_bias": city_bias,
            }
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Payload JSON khong hop le."},
            status=400,
        )
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


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
