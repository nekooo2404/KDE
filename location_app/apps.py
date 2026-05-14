from django.apps import AppConfig


class LocationAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'location_app'
    
    def ready(self):
        """Pre-load models and indexes on Django startup to avoid cold starts."""
        try:
            from .utils.semantic_inference import _get_embedding_model
            # Pre-load embedding model lazily (only if semantic inference is used)
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Pre-loading embedding model on startup...")
            _get_embedding_model()
            logger.info("✓ Embedding model pre-loaded")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not pre-load embedding model: {e}")

