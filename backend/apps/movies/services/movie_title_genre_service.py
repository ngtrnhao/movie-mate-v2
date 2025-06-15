import logging
from typing import Dict, Optional
from .tmdb_service import TMDBService

logger = logging.getLogger(__name__)

class MovieTitleGenreService:
    @classmethod
    def get_title_and_genres(cls, imdb_id: str, use_cache: bool = True) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Lấy title và genres cho cả tiếng Việt và tiếng Anh từ TMDB.
        Trả về:
        {
            "title": {"en": ..., "vi": ...},
            "genres": {"en": [...], "vi": [...]}
        }
        """
        try:
            tmdb_data = TMDBService.get_title_and_genres(imdb_id, use_cache=use_cache)
            return tmdb_data
        except Exception as e:
            logger.error(f"Error getting title/genres from TMDB: {str(e)}")
            return {
                "title": {"en": None, "vi": None},
                "genres": {"en": [], "vi": []}
            }
