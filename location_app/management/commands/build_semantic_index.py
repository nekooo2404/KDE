"""
Management command: Build semantic embeddings index for all cities.

Sử dụng sentence-transformers để encode tất cả cities + landmarks,
lưu embeddings vào database để dùng cho location inference.
"""

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from sentence_transformers import SentenceTransformer

from location_app.models import SemanticLocation
from location_app.utils.world_city_dataset import WorldCityDataset


class Command(BaseCommand):
    help = "Build semantic embeddings index for all major world cities"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default="sentence-transformers/all-MiniLM-L6-v2",
            help="Sentence-transformers model name (default: all-MiniLM-L6-v2)"
        )
        parser.add_argument(
            "--min-population",
            type=int,
            default=100_000,
            help="Minimum population to include in index (default: 100,000)"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=64,
            help="Batch size for encoding (default: 64)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force rebuild (delete existing embeddings first)"
        )
    
    def handle(self, *args, **options):
        model_name = options["model"]
        min_population = options["min_population"]
        batch_size = options["batch_size"]
        force = options["force"]
        
        self.stdout.write(f"Loading sentence-transformers model: {model_name}...")
        try:
            model = SentenceTransformer(model_name)
        except Exception as e:
            raise CommandError(f"Failed to load model: {e}")
        
        self.stdout.write("Loading world cities dataset...")
        try:
            dataset = WorldCityDataset()
        except Exception as e:
            raise CommandError(f"Failed to load dataset: {e}")
        
        # Filter cities by population
        cities_to_encode = []
        city_data_map = {}
        
        for i, row in enumerate(dataset.city_rows):
            population = int(row[8] or 0)
            if population < min_population:
                continue
            
            label = str(row[1])
            name = str(row[2])
            country = str(row[4])
            ascii_name = str(row[3])
            lat = float(dataset.latitudes[i])
            lon = float(dataset.longitudes[i])
            
            cities_to_encode.append({
                "label": label,
                "text": f"{name} {ascii_name} {country}"
            })
            city_data_map[label] = {
                "name": name,
                "country": country,
                "ascii_name": ascii_name,
                "lat": lat,
                "lon": lon,
                "population": population,
            }
        
        self.stdout.write(
            f"Found {len(cities_to_encode)} cities with population >= {min_population}"
        )
        
        if not cities_to_encode:
            raise CommandError("No cities found matching criteria")
        
        # Delete existing if force
        if force:
            self.stdout.write("Clearing existing embeddings...")
            SemanticLocation.objects.all().delete()
        
        # Encode in batches
        self.stdout.write("Encoding embeddings...")
        texts = [city["text"] for city in cities_to_encode]
        
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
            )
        except Exception as e:
            raise CommandError(f"Failed to encode embeddings: {e}")
        
        # Create/update SemanticLocation objects
        self.stdout.write("Saving embeddings to database...")
        created_count = 0
        updated_count = 0
        
        for city_info, embedding in zip(cities_to_encode, embeddings):
            label = city_info["label"]
            city_meta = city_data_map[label]
            
            # Convert embedding to JSON string
            embedding_json = json.dumps(embedding.tolist())
            
            # Semantic keywords based on city name and common associations
            landmarks = self._get_landmarks(label, city_meta["name"], city_meta["country"])
            
            obj, created = SemanticLocation.objects.update_or_create(
                city_label=label,
                defaults={
                    "city_name": city_meta["name"],
                    "country": city_meta["country"],
                    "latitude": city_meta["lat"],
                    "longitude": city_meta["lon"],
                    "population": city_meta["population"],
                    "embedding_json": embedding_json,
                    "landmarks": landmarks,
                    "coverage_score": self._compute_coverage_score(
                        embedding, city_meta["population"]
                    ),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Completed: {created_count} created, {updated_count} updated"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Total embeddings in database: {SemanticLocation.objects.count()}"
            )
        )
    
    def _get_landmarks(self, city_label: str, city_name: str, country: str) -> list[str]:
        """Generate semantic keywords for a city based on known landmarks."""
        landmarks_map = {
            "Paris": ["eiffel tower", "louvre", "notre-dame", "arc de triomphe", "champs elysees"],
            "London": ["big ben", "tower bridge", "buckingham palace", "westminster abbey"],
            "Tokyo": ["senso-ji", "meiji shrine", "shinjuku", "tsukiji", "shibuya"],
            "New York": ["times square", "empire state", "statue of liberty", "central park", "broadway"],
            "Sydney": ["opera house", "harbour bridge", "bondi beach"],
            "Rome": ["colosseum", "vatican", "pantheon", "trevi fountain"],
            "Barcelona": ["sagrada familia", "park guell", "gothic quarter"],
            "Amsterdam": ["anne frank house", "canal", "tulip"],
            "Bangkok": ["grand palace", "wat arun", "temple"],
            "Mumbai": ["taj mahal", "gateway of india", "bollywood"],
        }
        
        # Return specific landmarks if known, otherwise generate generic
        if city_name in landmarks_map:
            return landmarks_map[city_name]
        
        return [city_name.lower(), country.lower(), f"{city_name} city"]
    
    def _compute_coverage_score(self, embedding: Any, population: int) -> float:
        """Compute how well this location covers semantic space."""
        # Embedding norm as indicator of representativeness
        norm = (embedding ** 2).sum() ** 0.5
        norm_factor = min(1.0, norm / 10.0)  # Normalize
        
        # Population factor
        pop_factor = min(1.0, (population ** 0.5) / 1000)
        
        # Combined score
        return (norm_factor * 0.4 + pop_factor * 0.6)
