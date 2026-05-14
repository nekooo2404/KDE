from django.db import models


class LocationTerm(models.Model):
    term = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    density = models.FloatField(default=0.5)
    city = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.term} -> {self.city}"


class SemanticLocation(models.Model):
    """
    Semantic embeddings for cities + landmarks.
    Stores: location name, coordinates, embedding vector (quantized), cultural keywords.
    
    Quantized embeddings save 75% space: float32 (4 bytes) → int8 (1 byte)
    """
    city_label = models.CharField(max_length=100, unique=True, db_index=True)
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.IntegerField(default=0)
    
    # Embedding vector (store as JSON array for SQLite compatibility)
    # Can be float32 (full accuracy) or quantized int8 (compressed)
    embedding_json = models.TextField(help_text="JSON serialized embedding vector (float32 or int8)")
    
    # Quantization scale factors (for int8 dequantization)
    # Only used if embedding_json is int8 quantized
    embedding_min = models.TextField(
        default="null",
        help_text="JSON array of per-dimension min values (for int8 dequantization)"
    )
    embedding_max = models.TextField(
        default="null",
        help_text="JSON array of per-dimension max values (for int8 dequantization)"
    )
    
    # Semantic keywords/landmarks associated with this location
    landmarks = models.JSONField(
        default=list,
        help_text="List of landmark/cultural references"
    )
    
    # Confidence metrics
    coverage_score = models.FloatField(
        default=0.5,
        help_text="How well this location covers semantic space (0..1)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "location_semantic"
        ordering = ["-population"]
        indexes = [
            models.Index(fields=["city_label"]),
            models.Index(fields=["-population"]),
        ]
    
    def __str__(self):
        return f"{self.city_label} ({self.country})"


class LocationQuery(models.Model):
    """
    Log of location queries + results for analysis.
    Useful for tracking what works and what doesn't.
    """
    INFERENCE_METHOD_CHOICES = [
        ("semantic", "Semantic Embeddings"),
        ("tfidf", "TF-IDF Similarity"),
        ("llm", "LLM-based (Gemini)"),
    ]
    
    query_text = models.TextField()
    inferred_city = models.CharField(max_length=100, null=True, blank=True)
    inferred_lat = models.FloatField(null=True, blank=True)
    inferred_lon = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    method = models.CharField(
        max_length=20,
        choices=INFERENCE_METHOD_CHOICES,
        default="semantic"
    )
    keywords_extracted = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "location_query"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["method", "-created_at"]),
        ]
    
    def __str__(self):
        return f"{self.query_text[:50]} → {self.inferred_city}"
