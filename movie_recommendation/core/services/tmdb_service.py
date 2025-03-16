import requests
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class TMDbService:
    BASE_URL ="https://api.themoviedb.org/3/"

    def __init__(self,api_key=None):
        self.api_key = api_key or os.environ.get('TMDB_API_KEY') or  settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDb API key is required")

    def _make_request(self,endpoint,params=None):
        """Thực hiên request đến TMDb API"""
        if params is None:
            params = {}

        params['api_key'] = self.api_key
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.get(url,params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error making request to TMDb: {str(e)}")
            return None
    def get_movie_ratings(self,movie_id):
        """Lấy thông tin đánh giá từ TMDB"""
    def get_popular_movies(self,page=1):
        """Lấy danh sách phim phổ biến"""
        return self._make_request('movie/popular',{'page':page})

    def get_movie_by_id(self,movie_id):
        """Lấy thông tin chi tiết của phim"""
        return self._make_request(f'movie/{movie_id}',{'append_to_response':'credits,keywords'})
    def search_movies(self,query,page=1):
        """Tìm  kiếm sản phim theo từ khóa"""
        return self._make_request('search/movie',{'query':query,'page':page})
    def get_person_details(self,person_id):
        """Lấy thông tin chi tiết của người (diễn viên,đạo diễn...)"""
        return self._make_request(f'person/{person_id}',{'append_to_response':'movie_credits'})
    def discover_movies(self,params=None):
        """Khám  phá phim với các bộ lọc """
        if params is None:
            params = {}
        return self._make_request('discover/movie',params)