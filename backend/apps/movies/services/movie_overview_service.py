import logging
from typing import Dict, Optional

from .imdb_service import IMDBService
from .tmdb_service import TMDBService

logger = logging.getLogger(__name__)

class MovieOverviewService:
    @classmethod
    def get_movie_overview(cls, imdb_id: str, use_cache: bool = True) -> Dict[str, str]:
        """
        Get movie overview from TMDB only
        Returns a dictionary with language codes as keys and overviews as values
        """
        overviews = {}

        # Try TMDB
        try:
            tmdb_overviews = TMDBService.get_movie_overview(imdb_id, use_cache)
            if tmdb_overviews:
                overviews.update(tmdb_overviews)
        except Exception as e:
            logger.error(f"Error getting overview from TMDB: {str(e)}")

        # Ensure both languages are in the response, even if null
        if "vi" not in overviews:
            overviews["vi"] = None
        if "en" not in overviews:
            overviews["en"] = None

        # Log what we got for debugging
        logger.info(f"Overview for {imdb_id}: EN={bool(overviews.get('en'))}, VI={bool(overviews.get('vi'))}")

        # Comment out IMDB usage as API token is expired
        # if not all(lang in overviews for lang in ["vi", "en"]):
        #     try:
        #         imdb_overviews = IMDBService.get_movie_overview(imdb_id, use_cache)
        #         # Only update if the language is not already present
        #         for lang, text in imdb_overviews.items():
        #             if lang not in overviews:
        #                 overviews[lang] = text
        #     except Exception as e:
        #         logger.error(f"Error getting overview from IMDB: {str(e)}")

        return overviews
