import logging
import time
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from django.db import transaction
from apps.movies.models import Movie, MovieCast
from apps.movies.services.tmdb_service import TMDBService

logger = logging.getLogger(__name__)

class CastProfileEnrichmentService:
    """Service to enrich MovieCast records with profile images from TMDB"""

    def __init__(self):
        self.tmdb_service = TMDBService()
        self.image_base_url = "https://image.tmdb.org/t/p/w185"

    def similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0.0

        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        if name1 == name2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, name1, name2).ratio()

    def get_movie_credits(self, movie: Movie) -> Optional[Dict]:
        """Get cast and crew from TMDB for a movie"""
        if not movie.tmdb_id:
            logger.warning(f"Movie {movie.id} has no TMDB ID")
            return None

        return self.tmdb_service._make_request(f"/movie/{movie.tmdb_id}/credits")

    def match_cast_with_tmdb(self, imdb_cast: MovieCast, tmdb_cast_list: List[Dict]) -> Optional[Dict]:
        """Match IMDB cast member with TMDB cast member"""
        if not imdb_cast.name or not tmdb_cast_list:
            return None

        best_match = None
        best_score = 0.0

        for tmdb_person in tmdb_cast_list:
            tmdb_name = tmdb_person.get('name', '')
            score = self.similarity_score(imdb_cast.name, tmdb_name)

            # Exact match gets priority
            if score == 1.0:
                return tmdb_person

            # Good fuzzy match (threshold 0.8)
            if score > 0.8 and score > best_score:
                best_match = tmdb_person
                best_score = score

        # Only return if confidence is high enough
        return best_match if best_score > 0.8 else None

    def enrich_movie_cast_profiles(self, movie_id: int, limit: int = 20) -> Dict:
        """Enrich cast profiles for a specific movie"""
        try:
            movie = Movie.objects.get(id=movie_id)
            if not movie.tmdb_id:
                return {"success": False, "error": "Movie has no TMDB ID"}

            # Get TMDB credits
            credits = self.get_movie_credits(movie)
            if not credits:
                return {"success": False, "error": "Failed to fetch TMDB credits"}

            tmdb_cast = credits.get('cast', [])
            tmdb_crew = credits.get('crew', [])

            # Update actors
            actors = MovieCast.objects.filter(
                movie=movie,
                role='ACTOR',
                profile_path__isnull=True  # Only update empty profiles
            )[:limit]

            updated_count = 0
            for actor in actors:
                tmdb_match = self.match_cast_with_tmdb(actor, tmdb_cast)
                if tmdb_match and tmdb_match.get('profile_path'):
                    # Use detailed enrichment
                    if self.enrich_cast_with_tmdb_details(actor, tmdb_match):
                        updated_count += 1
                        logger.info(f"Updated profile for actor: {actor.name}")

                time.sleep(0.1)  # Rate limiting

            # Update directors and crew
            crew_members = MovieCast.objects.filter(
                movie=movie,
                role__in=['DIRECTOR', 'WRITER', 'PRODUCER'],
                profile_path__isnull=True
            )[:limit]

            for crew_member in crew_members:
                tmdb_match = self.match_cast_with_tmdb(crew_member, tmdb_crew)
                if tmdb_match and tmdb_match.get('profile_path'):
                    # Use detailed enrichment
                    if self.enrich_cast_with_tmdb_details(crew_member, tmdb_match):
                        updated_count += 1
                        logger.info(f"Updated profile for crew: {crew_member.name}")

                time.sleep(0.1)

            return {
                "success": True,
                "updated_count": updated_count,
                "movie_title": movie.title
            }

        except Movie.DoesNotExist:
            return {"success": False, "error": f"Movie {movie_id} not found"}
        except Exception as e:
            logger.error(f"Error enriching cast for movie {movie_id}: {e}")
            return {"success": False, "error": str(e)}

    def enrich_popular_movies(self, limit: int = 50) -> Dict:
        """Enrich cast profiles for popular movies"""

        # Get popular movies with TMDB ID and high ratings
        popular_movies = Movie.objects.filter(
            tmdb_id__isnull=False,
            cached_tmdb_rating__gte=7.0
        ).order_by('-cached_tmdb_rating')[:limit]

        total_updated = 0
        success_count = 0

        for movie in popular_movies:
            logger.info(f"Processing movie: {movie.title}")
            result = self.enrich_movie_cast_profiles(movie.id, limit=15)

            if result["success"]:
                success_count += 1
                total_updated += result["updated_count"]
                logger.info(f"✅ {movie.title}: {result['updated_count']} profiles updated")
            else:
                logger.error(f"❌ {movie.title}: {result['error']}")

            time.sleep(1)  # Rate limiting between movies

        return {
            "success": True,
            "movies_processed": success_count,
            "total_movies": len(popular_movies),
            "total_profiles_updated": total_updated
        }

    def enrich_cast_by_tmdb_id_mapping(self, batch_size: int = 10) -> Dict:
        """Alternative approach: Use movies with both IMDB and TMDB IDs"""

        # Get movies that have both IMDB and TMDB IDs
        movies_with_both_ids = Movie.objects.filter(
            imdb_id__isnull=False,
            tmdb_id__isnull=False,
            cached_tmdb_rating__gte=6.0  # Focus on decent movies
        ).order_by('-cached_tmdb_rating')[:batch_size]

        logger.info(f"Found {len(movies_with_both_ids)} movies with both IMDB and TMDB IDs")

        total_updated = 0
        for movie in movies_with_both_ids:
            result = self.enrich_movie_cast_profiles(movie.id)
            if result["success"]:
                total_updated += result["updated_count"]
                logger.info(f"Movie: {movie.title} - Updated: {result['updated_count']}")

            time.sleep(1)

        return {
            "success": True,
            "total_updated": total_updated,
            "movies_processed": len(movies_with_both_ids)
        }

    def get_tmdb_person_details(self, person_id: int) -> Optional[Dict]:
        """Get detailed person information from TMDB"""
        return self.tmdb_service._make_request(f"/person/{person_id}")

    def search_tmdb_person(self, name: str) -> Optional[Dict]:
        """Search for person on TMDB by name"""
        return self.tmdb_service._make_request("/search/person", {"query": name})

    def enrich_cast_with_tmdb_details(self, cast_member: MovieCast, tmdb_person: Dict) -> bool:
        """Enrich cast member with detailed TMDB information"""
        try:
            person_id = tmdb_person.get('id')
            if not person_id:
                return False

            # Get detailed person info
            person_details = self.get_tmdb_person_details(person_id)
            if not person_details:
                return False

            # Update cast member with TMDB details
            update_fields = ['profile_path']

            if tmdb_person.get('profile_path'):
                cast_member.profile_path = f"{self.image_base_url}{tmdb_person['profile_path']}"

            if person_details.get('id'):
                cast_member.tmdb_id = person_details['id']
                update_fields.append('tmdb_id')

            if person_details.get('biography'):
                cast_member.biography = person_details['biography']
                update_fields.append('biography')

            if person_details.get('place_of_birth'):
                cast_member.place_of_birth = person_details['place_of_birth']
                update_fields.append('place_of_birth')

            if person_details.get('gender'):
                cast_member.gender = person_details['gender']
                update_fields.append('gender')

            if person_details.get('popularity'):
                cast_member.popularity = person_details['popularity']
                update_fields.append('popularity')

            cast_member.save(update_fields=update_fields)
            return True

        except Exception as e:
            logger.error(f"Error enriching cast member {cast_member.name}: {e}")
            return False
