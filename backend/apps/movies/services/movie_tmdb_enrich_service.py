from apps.movies.services.tmdb_service import TMDBService
from apps.movies.models import Movie, MovieMetadata, MovieImage, MovieTrailer, MovieRating, MovieReview, MovieBoxOffice

class MovieTMDBEnrichService:
    @classmethod
    def enrich_backdrop_and_tmdb_id(cls, movie):
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_movie_details(int(movie.tmdb_id)) if getattr(movie, 'tmdb_id', None) else None
        if not tmdb_data and movie.imdb_id:
            find_result = tmdb_service._make_request(f"find/{movie.imdb_id}", {"external_source": "imdb_id"})
            if find_result and find_result.get("movie_results"):
                tmdb_id = find_result["movie_results"][0]["id"]
                movie.tmdb_id = tmdb_id
                tmdb_data = tmdb_service.get_movie_details(tmdb_id)
        if tmdb_data:
            movie.backdrop_url = f"https://image.tmdb.org/t/p/original{tmdb_data.get('backdrop_path')}" if tmdb_data.get('backdrop_path') else None
            movie.save()

    @classmethod
    def enrich_movie_metadata(cls, movie):
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_movie_details(int(getattr(movie, 'tmdb_id', None))) if getattr(movie, 'tmdb_id', None) else None
        if not tmdb_data:
            return
        metadata, _ = MovieMetadata.objects.get_or_create(movie=movie)
        metadata.budget = tmdb_data.get("budget")
        metadata.revenue = tmdb_data.get("revenue")
        metadata.tagline = tmdb_data.get("tagline")
        metadata.homepage = tmdb_data.get("homepage")
        metadata.keywords = [kw["name"] for kw in tmdb_data.get("keywords", {}).get("keywords", [])] if "keywords" in tmdb_data else []
        metadata.production_companies = tmdb_data.get("production_companies")
        metadata.production_countries = tmdb_data.get("production_countries")
        metadata.spoken_languages = tmdb_data.get("spoken_languages")
        metadata.save()

    @classmethod
    def enrich_movie_images(cls, movie):
        tmdb_service = TMDBService()
        images_data = tmdb_service._make_request(f"movie/{getattr(movie, 'tmdb_id', None)}/images")
        if not images_data:
            return
        for poster in images_data.get("posters", []):
            MovieImage.objects.get_or_create(
                movie=movie,
                image_url=f"https://image.tmdb.org/t/p/w500{poster['file_path']}",
                type="POSTER",
                width=poster.get("width"),
                height=poster.get("height"),
                aspect_ratio=poster.get("aspect_ratio"),
            )
        for backdrop in images_data.get("backdrops", []):
            MovieImage.objects.get_or_create(
                movie=movie,
                image_url=f"https://image.tmdb.org/t/p/original{backdrop['file_path']}",
                type="BACKDROP",
                width=backdrop.get("width"),
                height=backdrop.get("height"),
                aspect_ratio=backdrop.get("aspect_ratio"),
            )

    @classmethod
    def enrich_movie_trailers(cls, movie):
        tmdb_service = TMDBService()
        videos_data = tmdb_service._make_request(f"movie/{getattr(movie, 'tmdb_id', None)}/videos")
        if not videos_data:
            return
        for video in videos_data.get("results", []):
            if video["site"] == "YouTube":
                MovieTrailer.objects.get_or_create(
                    movie=movie,
                    title=video["name"],
                    youtube_key=video["key"],
                    type=video["type"].upper() if video["type"] in ["Trailer", "Teaser", "Clip"] else "TRAILER"
                )

    @classmethod
    def enrich_movie_rating(cls, movie):
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_movie_details(int(getattr(movie, 'tmdb_id', None))) if getattr(movie, 'tmdb_id', None) else None
        if not tmdb_data:
            return
        MovieRating.objects.update_or_create(
            movie=movie,
            defaults={
                "tmdb_rating": tmdb_data.get("vote_average"),
                "tmdb_votes": tmdb_data.get("vote_count"),
            }
        )

    @classmethod
    def enrich_movie_reviews(cls, movie):
        tmdb_service = TMDBService()
        reviews_data = tmdb_service._make_request(f"movie/{getattr(movie, 'tmdb_id', None)}/reviews")
        if not reviews_data:
            return
        for review in reviews_data.get("results", []):
            MovieReview.objects.get_or_create(
                movie=movie,
                username=review.get("author"),
                title=review.get("author_details", {}).get("username", ""),
                content=review.get("content"),
                rating=review.get("author_details", {}).get("rating"),
                source="TMDB",
                source_url=review.get("url"),
                published_at=review.get("created_at"),
            )

    @classmethod
    def enrich_movie_box_office(cls, movie):
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_movie_details(int(getattr(movie, 'tmdb_id', None))) if getattr(movie, 'tmdb_id', None) else None
        if not tmdb_data:
            return
        MovieBoxOffice.objects.update_or_create(
            movie=movie,
            defaults={
                "budget": tmdb_data.get("budget"),
                "domestic_gross": None,  # TMDB không có, có thể lấy từ nguồn khác
                "foreign_gross": None,
                "worldwide_gross": tmdb_data.get("revenue"),
            }
        )

    @classmethod
    def enrich_all(cls, movie):
        cls.enrich_backdrop_and_tmdb_id(movie)
        cls.enrich_movie_metadata(movie)
        cls.enrich_movie_images(movie)
        cls.enrich_movie_trailers(movie)
        cls.enrich_movie_rating(movie)
        cls.enrich_movie_reviews(movie)
        cls.enrich_movie_box_office(movie)
