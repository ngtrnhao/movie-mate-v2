import logging
import time
from typing import Dict, List, Optional, Tuple, Union
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .tmdb_service import TMDBService
from .imdb_service import IMDBService
from .movie_title_genre_service import MovieTitleGenreService
from .movie_overview_service import MovieOverviewService
from .movie_tmdb_enrich_service import MovieTMDBEnrichService
from .quality_calculation_service import QualityCalculationService
from .cast_profile_enrichment_service import CastProfileEnrichmentService
from ..models import Movie, MovieQualityMetrics, MovieImage, MovieTrailer, MovieCast

logger = logging.getLogger(__name__)


class UnifiedMovieEnrichmentService:
    """
    🎬 Unified Movie Enrichment Service

    Đồng bộ tất cả các services lấy thông tin phim từ TMDB/IMDB:
    - Title và Overview đa ngôn ngữ (EN/VI)
    - Poster, Backdrop, và media assets
    - Cast, Crew và character information
    - Ratings từ multiple sources
    - Genres, Keywords, Production info
    - Trailers và videos
    - Quality assessment và suggestions

    Được thiết kế đặc biệt cho Admin Dashboard để:
    - Xử lý Quality Issues tự động
    - Bổ sung thông tin thiếu dựa trên Quality Suggestions
    - Mapping TMDB ID từ IMDB ID
    - Batch processing cho multiple movies
    """

    def __init__(self):
        self.tmdb_service = TMDBService()
        self.imdb_service = IMDBService()
        self.title_genre_service = MovieTitleGenreService()
        self.overview_service = MovieOverviewService()
        self.tmdb_enrich_service = MovieTMDBEnrichService()
        self.quality_service = QualityCalculationService()

        # Rate limiting cho external APIs
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.batch_delay = 2.0       # 2s between batches

    # ===========================================
    # CORE ENRICHMENT METHODS
    # ===========================================

    def enrich_movie_comprehensive(
        self,
        movie: Movie,
        force_refresh: bool = False,
        focus_areas: List[str] = None
    ) -> Dict:
        """
        Main method: Comprehensive movie enrichment

        Args:
            movie: Movie instance to enrich
            force_refresh: Force fetch new data even if exists
            focus_areas: Specific areas to focus on ['basic', 'visual', 'metadata', 'ratings']
                        None = enrich all areas

        Returns:
            Dict: Enrichment results with success/failure details
        """
        start_time = time.time()
        results = {
            'movie_id': movie.id,
            'movie_title': movie.title,
            'success': False,
            'operations': {},
            'errors': [],
            'improvements': [],
            'quality_before': None,
            'quality_after': None,
            'processing_time': 0
        }

        try:
            # Get initial quality metrics
            initial_quality = self._get_current_quality_metrics(movie)
            results['quality_before'] = initial_quality

            # Determine enrichment strategy based on quality issues
            enrichment_plan = self._create_enrichment_plan(movie, focus_areas, force_refresh)

            logger.info(f"🎬 Starting comprehensive enrichment for movie {movie.id}: {movie.title}")
            logger.info(f"📋 Enrichment plan: {enrichment_plan}")

            # Execute enrichment plan
            with transaction.atomic():
                # Step 1: Ensure TMDB ID mapping
                if enrichment_plan.get('ensure_tmdb_id', False):
                    tmdb_result = self._ensure_tmdb_id_mapping(movie)
                    results['operations']['tmdb_id_mapping'] = tmdb_result
                    time.sleep(self.rate_limit_delay)

                # Step 2: Basic information (titles, overviews)
                if enrichment_plan.get('enrich_basic_info', False):
                    basic_result = self._enrich_basic_information(movie, force_refresh)
                    results['operations']['basic_info'] = basic_result
                    time.sleep(self.rate_limit_delay)

                # Step 3: Visual assets (posters, backdrops)
                if enrichment_plan.get('enrich_visual_assets', False):
                    visual_result = self._enrich_visual_assets(movie, force_refresh)
                    results['operations']['visual_assets'] = visual_result
                    time.sleep(self.rate_limit_delay)

                # Step 4: Metadata richness (cast, genres, trailers)
                if enrichment_plan.get('enrich_metadata', False):
                    metadata_result = self._enrich_metadata_richness(movie, force_refresh)
                    results['operations']['metadata'] = metadata_result
                    time.sleep(self.rate_limit_delay)

                # Step 5: Rating information
                if enrichment_plan.get('enrich_ratings', False):
                    rating_result = self._enrich_rating_information(movie, force_refresh)
                    results['operations']['ratings'] = rating_result
                    time.sleep(self.rate_limit_delay)

                # Step 6: Additional TMDB enrichment
                if enrichment_plan.get('enrich_additional_tmdb', False):
                    additional_result = self._enrich_additional_tmdb_data(movie)
                    results['operations']['additional_tmdb'] = additional_result

            # Recalculate quality metrics after enrichment
            final_quality = self.quality_service.calculate_movie_quality(movie, save=True)
            results['quality_after'] = final_quality

            # Calculate improvements
            improvements = self._calculate_improvements(initial_quality, final_quality)
            results['improvements'] = improvements

            # Mark as successful if any operation succeeded
            success_operations = [op for op in results['operations'].values() if op.get('success', False)]
            results['success'] = len(success_operations) > 0

            processing_time = time.time() - start_time
            results['processing_time'] = round(processing_time, 2)

            logger.info(f"✅ Enrichment completed for movie {movie.id} in {processing_time:.2f}s")
            logger.info(f"📊 Quality score: {initial_quality.get('quality_score', 'N/A')} → {final_quality.get('quality_score', 'N/A')}")

            return results

        except Exception as e:
            logger.error(f"❌ Error during comprehensive enrichment for movie {movie.id}: {str(e)}")
            results['errors'].append(f"Comprehensive enrichment failed: {str(e)}")
            results['processing_time'] = time.time() - start_time
            return results

    def enrich_movie_by_quality_issues(self, movie: Movie) -> Dict:
        """
        🎯 Targeted enrichment based on specific quality issues

        This method analyzes current quality issues and only enriches
        the specific areas that need improvement.
        """
        try:
            # Get current quality metrics and issues
            quality_metrics = self._get_current_quality_metrics(movie)
            quality_issues = quality_metrics.get('quality_issues', [])

            if not quality_issues:
                logger.info(f"🎉 Movie {movie.id} has no quality issues - skipping targeted enrichment")
                return {
                    'success': True,
                    'message': 'No quality issues found',
                    'operations': {}
                }

            logger.info(f"🎯 Targeting quality issues for movie {movie.id}: {quality_issues}")

            # Map quality issues to enrichment actions
            focus_areas = self._map_quality_issues_to_focus_areas(quality_issues)

            # Perform targeted enrichment
            return self.enrich_movie_comprehensive(
                movie=movie,
                force_refresh=False,  # Don't force refresh for targeted enrichment
                focus_areas=focus_areas
            )

        except Exception as e:
            logger.error(f"❌ Error in quality-based enrichment for movie {movie.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'operations': {}
            }

    def batch_enrich_movies(
        self,
        movie_ids: List[int],
        focus_areas: List[str] = None,
        max_concurrent: int = 5
    ) -> Dict:
        """
        🚀 Batch enrichment for multiple movies

        Args:
            movie_ids: List of movie IDs to enrich
            focus_areas: Areas to focus enrichment on
            max_concurrent: Maximum concurrent processing (rate limiting)

        Returns:
            Dict: Batch processing results
        """
        start_time = time.time()
        batch_results = {
            'total_movies': len(movie_ids),
            'processed_successfully': 0,
            'errors': 0,
            'results': [],
            'processing_time': 0,
            'success_rate': 0
        }

        logger.info(f"🚀 Starting batch enrichment for {len(movie_ids)} movies")

        try:
            # Process in chunks to avoid overwhelming APIs
            chunk_size = min(max_concurrent, 10)

            for i in range(0, len(movie_ids), chunk_size):
                chunk_ids = movie_ids[i:i + chunk_size]
                chunk_results = self._process_movie_chunk(chunk_ids, focus_areas)

                # Aggregate results
                for result in chunk_results:
                    batch_results['results'].append(result)
                    if result.get('success', False):
                        batch_results['processed_successfully'] += 1
                    else:
                        batch_results['errors'] += 1

                # Rate limiting between chunks
                if i + chunk_size < len(movie_ids):
                    logger.info(f"⏸️  Batch delay between chunks: {self.batch_delay}s")
                    time.sleep(self.batch_delay)

            # Calculate final metrics
            processing_time = time.time() - start_time
            batch_results['processing_time'] = round(processing_time, 2)
            batch_results['success_rate'] = round(
                (batch_results['processed_successfully'] / batch_results['total_movies']) * 100, 2
            ) if batch_results['total_movies'] > 0 else 0

            logger.info(f"✅ Batch enrichment completed in {processing_time:.2f}s")
            logger.info(f"📊 Success rate: {batch_results['success_rate']}% ({batch_results['processed_successfully']}/{batch_results['total_movies']})")

            return batch_results

        except Exception as e:
            logger.error(f"❌ Error in batch enrichment: {str(e)}")
            batch_results['processing_time'] = time.time() - start_time
            return batch_results

    # ===========================================
    # TMDB ID MAPPING & CORE DATA METHODS
    # ===========================================

    def _ensure_tmdb_id_mapping(self, movie: Movie) -> Dict:
        """
        🔍 Ensure movie has TMDB ID mapped from IMDB ID

        Critical for accessing TMDB API data when movies are imported
        from IMDB dataset but lack TMDB integration.
        """
        try:
            if movie.tmdb_id:
                return {
                    'success': True,
                    'message': f'TMDB ID already exists: {movie.tmdb_id}',
                    'tmdb_id': movie.tmdb_id,
                    'action': 'skipped'
                }

            if not movie.imdb_id:
                return {
                    'success': False,
                    'message': 'No IMDB ID available for TMDB mapping',
                    'action': 'failed'
                }

            logger.info(f"🔍 Mapping TMDB ID for movie {movie.id} using IMDB ID: {movie.imdb_id}")

            # Get TMDB ID from IMDB ID
            tmdb_id = self.tmdb_service.get_tmdb_id_from_imdb(movie.imdb_id)

            if tmdb_id:
                movie.tmdb_id = str(tmdb_id)
                movie.save(update_fields=['tmdb_id'])

                logger.info(f"✅ Successfully mapped TMDB ID: {movie.imdb_id} → {tmdb_id}")
                return {
                    'success': True,
                    'message': f'Successfully mapped TMDB ID: {tmdb_id}',
                    'tmdb_id': tmdb_id,
                    'action': 'mapped'
                }
            else:
                logger.warning(f"⚠️  Could not find TMDB ID for IMDB ID: {movie.imdb_id}")
                return {
                    'success': False,
                    'message': f'TMDB ID not found for IMDB ID: {movie.imdb_id}',
                    'action': 'not_found'
                }

        except Exception as e:
            logger.error(f"❌ Error mapping TMDB ID for movie {movie.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error mapping TMDB ID: {str(e)}',
                'action': 'error'
            }

    def _enrich_basic_information(self, movie: Movie, force_refresh: bool = False) -> Dict:
        """
        Enrich basic movie information (titles, overviews, release date)
        """
        results = {
            'success': False,
            'operations': {},
            'improved_fields': []
        }

        try:
            # Enrich titles (EN/VI)
            if force_refresh or not movie.title_en or not movie.title_vi:
                title_result = self._enrich_titles(movie)
                results['operations']['titles'] = title_result
                if title_result.get('success'):
                    results['improved_fields'].extend(title_result.get('updated_fields', []))

            # Enrich overviews (EN/VI)
            if force_refresh or not movie.overview_en or not movie.overview_vi:
                overview_result = self._enrich_overviews(movie)
                results['operations']['overviews'] = overview_result
                if overview_result.get('success'):
                    results['improved_fields'].extend(overview_result.get('updated_fields', []))

            # Enrich basic metadata from TMDB
            if movie.tmdb_id:
                metadata_result = self._enrich_basic_metadata(movie, force_refresh)
                results['operations']['basic_metadata'] = metadata_result
                if metadata_result.get('success'):
                    results['improved_fields'].extend(metadata_result.get('updated_fields', []))

            # Mark as successful if any operation succeeded
            results['success'] = any(op.get('success', False) for op in results['operations'].values())

            logger.info(f"📝 Basic information enrichment for movie {movie.id}: {results['success']}")
            return results

        except Exception as e:
            logger.error(f"❌ Error enriching basic information for movie {movie.id}: {str(e)}")
            results['error'] = str(e)
            return results

    def _enrich_visual_assets(self, movie: Movie, force_refresh: bool = False) -> Dict:
        """
        Enrich visual assets (poster, backdrop, additional images)
        """
        results = {
            'success': False,
            'operations': {},
            'improved_fields': []
        }

        try:
            # Ensure we have TMDB ID for visual assets
            if not movie.tmdb_id:
                tmdb_mapping = self._ensure_tmdb_id_mapping(movie)
                if not tmdb_mapping.get('success'):
                    return {
                        'success': False,
                        'error': 'Cannot enrich visual assets without TMDB ID'
                    }

            # Enrich poster and backdrop
            if force_refresh or not movie.poster_url or not movie.backdrop_url:
                visual_result = self._enrich_poster_backdrop(movie)
                results['operations']['poster_backdrop'] = visual_result
                if visual_result.get('success'):
                    results['improved_fields'].extend(visual_result.get('updated_fields', []))

            # Enrich additional images
            images_result = self._enrich_additional_images(movie)
            results['operations']['additional_images'] = images_result
            if images_result.get('success'):
                results['improved_fields'].append('additional_images')

            results['success'] = any(op.get('success', False) for op in results['operations'].values())

            logger.info(f"🖼️ Visual assets enrichment for movie {movie.id}: {results['success']}")
            return results

        except Exception as e:
            logger.error(f"❌ Error enriching visual assets for movie {movie.id}: {str(e)}")
            results['error'] = str(e)
            return results

    def _enrich_metadata_richness(self, movie: Movie, force_refresh: bool = False) -> Dict:
        """
        Enrich metadata richness (cast, genres, trailers, keywords)
        """
        results = {
            'success': False,
            'operations': {},
            'improved_fields': []
        }

        try:
            # Enrich genres
            if force_refresh or movie.genres.count() == 0:
                genre_result = self._enrich_genres(movie)
                results['operations']['genres'] = genre_result
                if genre_result.get('success'):
                    results['improved_fields'].append('genres')

            # Enrich cast information
            if force_refresh or movie.cast.count() == 0:
                cast_result = self._enrich_cast_information(movie)
                results['operations']['cast'] = cast_result
                if cast_result.get('success'):
                    results['improved_fields'].append('cast')

            # Enrich trailers
            if force_refresh or movie.trailers.count() == 0:
                trailer_result = self._enrich_trailers(movie)
                results['operations']['trailers'] = trailer_result
                if trailer_result.get('success'):
                    results['improved_fields'].append('trailers')

            # Enrich additional metadata (keywords, production info)
            if movie.tmdb_id:
                additional_result = self._enrich_additional_metadata(movie)
                results['operations']['additional_metadata'] = additional_result
                if additional_result.get('success'):
                    results['improved_fields'].append('additional_metadata')

            results['success'] = any(op.get('success', False) for op in results['operations'].values())

            logger.info(f"🎭 Metadata richness enrichment for movie {movie.id}: {results['success']}")
            return results

        except Exception as e:
            logger.error(f"❌ Error enriching metadata richness for movie {movie.id}: {str(e)}")
            results['error'] = str(e)
            return results

    def _enrich_rating_information(self, movie: Movie, force_refresh: bool = False) -> Dict:
        """
        Enrich rating information from multiple sources
        """
        results = {
            'success': False,
            'operations': {},
            'improved_fields': []
        }

        try:
            # Update cached ratings from existing data
            rating_result = self._update_cached_ratings(movie)
            results['operations']['cached_ratings'] = rating_result
            if rating_result.get('success'):
                results['improved_fields'].extend(rating_result.get('updated_fields', []))

            # Enrich TMDB ratings
            if movie.tmdb_id:
                tmdb_rating_result = self._enrich_tmdb_ratings(movie)
                results['operations']['tmdb_ratings'] = tmdb_rating_result
                if tmdb_rating_result.get('success'):
                    results['improved_fields'].append('tmdb_ratings')

            results['success'] = any(op.get('success', False) for op in results['operations'].values())

            logger.info(f"⭐ Rating information enrichment for movie {movie.id}: {results['success']}")
            return results

        except Exception as e:
            logger.error(f"❌ Error enriching rating information for movie {movie.id}: {str(e)}")
            results['error'] = str(e)
            return results

    def _enrich_additional_tmdb_data(self, movie: Movie) -> Dict:
        """
        Use existing MovieTMDBEnrichService for comprehensive TMDB data
        """
        try:
            if not movie.tmdb_id:
                return {
                    'success': False,
                    'message': 'No TMDB ID available for additional enrichment'
                }

            # Use existing service for additional enrichment
            self.tmdb_enrich_service.enrich_all(movie)

            return {
                'success': True,
                'message': 'Additional TMDB data enriched successfully',
                'enriched_data': ['metadata', 'images', 'trailers', 'ratings', 'reviews', 'box_office']
            }

        except Exception as e:
            logger.error(f"❌ Error in additional TMDB enrichment for movie {movie.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ===========================================
    # HELPER METHODS FOR SPECIFIC DATA TYPES
    # ===========================================

    def _enrich_titles(self, movie: Movie) -> Dict:
        """Enrich movie titles in multiple languages"""
        try:
            if not movie.imdb_id:
                return {'success': False, 'message': 'No IMDB ID for title enrichment'}

            title_data = self.title_genre_service.get_title_and_genres(movie.imdb_id)
            titles = title_data.get('title', {})

            updated_fields = []

            # Always try to update both languages if we have data
            if titles.get('en') and titles['en'] != movie.title_en:
                movie.title_en = titles['en']
                updated_fields.append('title_en')
                logger.info(f"Updated EN title for movie {movie.id}: {titles['en']}")

            if titles.get('vi') and titles['vi'] != movie.title_vi:
                movie.title_vi = titles['vi']
                updated_fields.append('title_vi')
                logger.info(f"Updated VI title for movie {movie.id}: {titles['vi']}")

            # Log what we got vs what we had
            logger.info(f"Movie {movie.id} titles - EN: {titles.get('en')} vs {movie.title_en}, VI: {titles.get('vi')} vs {movie.title_vi}")

            if updated_fields:
                # If title changed, we need to update slug too
                if 'title' in updated_fields:
                    # Force slug regeneration by setting it to None
                    movie.slug = None
                    updated_fields.append('slug')

                movie.save(update_fields=updated_fields + ['updated_at'])
                return {
                    'success': True,
                    'message': f'Updated titles: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }

            return {'success': False, 'message': 'No new title data available'}

        except Exception as e:
            logger.error(f"❌ Error enriching titles for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_overviews(self, movie: Movie) -> Dict:
        """Enrich movie overviews in multiple languages"""
        try:
            if not movie.imdb_id:
                return {'success': False, 'message': 'No IMDB ID for overview enrichment'}

            overviews = self.overview_service.get_movie_overview(movie.imdb_id)

            updated_fields = []

            # Always try to update both languages if we have data
            if overviews.get('en') and overviews['en'] != movie.overview_en:
                movie.overview_en = overviews['en']
                updated_fields.append('overview_en')
                logger.info(f"Updated EN overview for movie {movie.id}")

            if overviews.get('vi') and overviews['vi'] != movie.overview_vi:
                movie.overview_vi = overviews['vi']
                updated_fields.append('overview_vi')
                logger.info(f"Updated VI overview for movie {movie.id}")

            # Log what we got vs what we had
            logger.info(f"Movie {movie.id} overviews - EN: {bool(overviews.get('en'))} vs {bool(movie.overview_en)}, VI: {bool(overviews.get('vi'))} vs {bool(movie.overview_vi)}")

            if updated_fields:
                movie.save(update_fields=updated_fields + ['updated_at'])
                return {
                    'success': True,
                    'message': f'Updated overviews: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }

            return {'success': False, 'message': 'No new overview data available'}

        except Exception as e:
            logger.error(f"❌ Error enriching overviews for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_basic_metadata(self, movie: Movie, force_refresh: bool = False) -> Dict:
        """Enrich basic metadata from TMDB"""
        try:
            if not movie.tmdb_id:
                return {'success': False, 'message': 'No TMDB ID for metadata enrichment'}

            tmdb_data = self.tmdb_service.get_movie_details(int(movie.tmdb_id))
            if not tmdb_data:
                return {'success': False, 'message': 'Failed to fetch TMDB data'}

            updated_fields = []

            # Update runtime if missing
            if tmdb_data.get('runtime') and (not movie.runtime or force_refresh):
                movie.runtime = tmdb_data['runtime']
                updated_fields.append('runtime')

            # Update release date if missing
            if tmdb_data.get('release_date') and (not movie.release_date or force_refresh):
                from datetime import datetime
                try:
                    movie.release_date = datetime.strptime(tmdb_data['release_date'], '%Y-%m-%d').date()
                    updated_fields.append('release_date')
                except ValueError:
                    pass

            # Update original title if missing
            if tmdb_data.get('original_title') and (not movie.original_title or force_refresh):
                movie.original_title = tmdb_data['original_title']
                updated_fields.append('original_title')

            if updated_fields:
                movie.save(update_fields=updated_fields + ['updated_at'])
                return {
                    'success': True,
                    'message': f'Updated metadata: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }

            return {'success': False, 'message': 'No new metadata available'}

        except Exception as e:
            logger.error(f"❌ Error enriching basic metadata for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_poster_backdrop(self, movie: Movie) -> Dict:
        """Enrich poster and backdrop URLs"""
        try:
            if not movie.tmdb_id:
                return {'success': False, 'message': 'No TMDB ID for visual assets'}

            tmdb_data = self.tmdb_service.get_movie_details(int(movie.tmdb_id))
            if not tmdb_data:
                return {'success': False, 'message': 'Failed to fetch TMDB data'}

            updated_fields = []
            base_url = "https://image.tmdb.org/t/p/original"

            # Update poster
            if tmdb_data.get('poster_path') and not movie.poster_url:
                movie.poster_url = f"{base_url}{tmdb_data['poster_path']}"
                updated_fields.append('poster_url')

            # Update backdrop
            if tmdb_data.get('backdrop_path') and not movie.backdrop_url:
                movie.backdrop_url = f"{base_url}{tmdb_data['backdrop_path']}"
                updated_fields.append('backdrop_url')

            if updated_fields:
                movie.save(update_fields=updated_fields + ['updated_at'])
                return {
                    'success': True,
                    'message': f'Updated visual assets: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }

            return {'success': False, 'message': 'No new visual assets available'}

        except Exception as e:
            logger.error(f"❌ Error enriching visual assets for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_additional_images(self, movie: Movie) -> Dict:
        """Enrich additional movie images"""
        try:
            # Use existing TMDB enrich service
            self.tmdb_enrich_service.enrich_movie_images(movie)
            return {
                'success': True,
                'message': 'Additional images enriched successfully'
            }
        except Exception as e:
            logger.error(f"❌ Error enriching additional images for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_genres(self, movie: Movie) -> Dict:
        """Enrich movie genres"""
        try:
            if not movie.imdb_id:
                return {'success': False, 'message': 'No IMDB ID for genre enrichment'}

            title_genre_data = self.title_genre_service.get_title_and_genres(movie.imdb_id)
            genres = title_genre_data.get('genres', {})

            if genres:
                # Log what we got
                logger.info(f"Movie {movie.id} genres - EN: {genres.get('en', [])}, VI: {genres.get('vi', [])}")

                success = movie.update_genres(genres)
                if success:
                    # Get updated genres to show what was actually added
                    updated_genres = list(movie.genres.values_list('name', 'language'))
                    en_genres = [name for name, lang in updated_genres if lang == 'en']
                    vi_genres = [name for name, lang in updated_genres if lang == 'vi']

                    logger.info(f"Updated genres for movie {movie.id}: EN={en_genres}, VI={vi_genres}")

                    return {
                        'success': True,
                        'message': f'Updated genres: {len(en_genres)} EN, {len(vi_genres)} VI'
                    }

            return {'success': False, 'message': 'No new genre data available'}

        except Exception as e:
            logger.error(f"❌ Error enriching genres for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_cast_information(self, movie: Movie) -> Dict:
        """Enrich cast and crew information, bao gồm enrich profile_path cho cast"""
        try:
            # Use existing TMDB enrich service for cast
            if not movie.tmdb_id:
                return {'success': False, 'message': 'No TMDB ID for cast enrichment'}

            # Enrich cast thông thường (nếu có logic ở TMDBEnrichService)
            # (Giữ lại logic cũ nếu có)
            # Gọi enrich profile_path cho cast chưa có profile_path
            cast_profile_result = CastProfileEnrichmentService().enrich_movie_cast_profiles(movie.id, limit=20)
            updated_count = cast_profile_result.get('updated_count', 0)
            if cast_profile_result.get('success'):
                msg = f"Cast enrichment (profile_path) completed: {updated_count} profiles updated"
                logger.info(msg)
                return {
                    'success': True,
                    'message': msg,
                    'updated_profiles': updated_count
                }
            else:
                msg = f"Cast enrichment (profile_path) failed: {cast_profile_result.get('error')}"
                logger.error(msg)
                return {
                    'success': False,
                    'message': msg
                }
        except Exception as e:
            logger.error(f"❌ Error enriching cast for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_trailers(self, movie: Movie) -> Dict:
        """Enrich movie trailers"""
        try:
            # Use existing TMDB enrich service
            self.tmdb_enrich_service.enrich_movie_trailers(movie)
            return {
                'success': True,
                'message': 'Trailers enriched successfully'
            }
        except Exception as e:
            logger.error(f"❌ Error enriching trailers for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_additional_metadata(self, movie: Movie) -> Dict:
        """Enrich additional metadata (keywords, production info)"""
        try:
            # Use existing TMDB enrich service
            self.tmdb_enrich_service.enrich_movie_metadata(movie)
            return {
                'success': True,
                'message': 'Additional metadata enriched successfully'
            }
        except Exception as e:
            logger.error(f"❌ Error enriching additional metadata for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _update_cached_ratings(self, movie: Movie) -> Dict:
        """Update cached rating fields for performance (không cần source, lấy từng trường theo tên)"""
        try:
            updated_fields = []
            ratings = movie.ratings.order_by('-id').first()
            if ratings:
                if ratings.imdb_rating and ratings.imdb_rating != movie.cached_imdb_rating:
                    movie.cached_imdb_rating = ratings.imdb_rating
                    updated_fields.append('cached_imdb_rating')
                if ratings.imdb_votes and ratings.imdb_votes != movie.cached_imdb_votes:
                    movie.cached_imdb_votes = ratings.imdb_votes
                    updated_fields.append('cached_imdb_votes')
                if ratings.tmdb_rating and ratings.tmdb_rating != movie.cached_tmdb_rating:
                    movie.cached_tmdb_rating = ratings.tmdb_rating
                    updated_fields.append('cached_tmdb_rating')
                if ratings.tmdb_votes and ratings.tmdb_votes != movie.cached_tmdb_votes:
                    movie.cached_tmdb_votes = ratings.tmdb_votes
                    updated_fields.append('cached_tmdb_votes')
            if updated_fields:
                movie.save(update_fields=updated_fields + ['updated_at'])
                return {
                    'success': True,
                    'message': f'Updated cached ratings: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }
            return {'success': False, 'message': 'No rating updates needed'}
        except Exception as e:
            logger.error(f"❌ Error updating cached ratings for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _enrich_tmdb_ratings(self, movie: Movie) -> Dict:
        """Enrich TMDB ratings"""
        try:
            # Use existing TMDB enrich service
            self.tmdb_enrich_service.enrich_movie_rating(movie)
            return {
                'success': True,
                'message': 'TMDB ratings enriched successfully'
            }
        except Exception as e:
            logger.error(f"❌ Error enriching TMDB ratings for movie {movie.id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ===========================================
    # PLANNING AND ANALYSIS METHODS
    # ===========================================

    def _create_enrichment_plan(
        self,
        movie: Movie,
        focus_areas: List[str] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        📋 Create intelligent enrichment plan based on current data state

        Args:
            movie: Movie to analyze
            focus_areas: Specific areas to focus on
            force_refresh: Force refresh existing data

        Returns:
            Dict: Enrichment plan with boolean flags for each operation
        """
        plan = {
            'ensure_tmdb_id': False,
            'enrich_basic_info': False,
            'enrich_visual_assets': False,
            'enrich_metadata': False,
            'enrich_ratings': False,
            'enrich_additional_tmdb': False
        }

        # Always ensure TMDB ID if missing
        if not movie.tmdb_id and movie.imdb_id:
            plan['ensure_tmdb_id'] = True

        # If focus_areas specified, only enrich those areas
        if focus_areas:
            for area in focus_areas:
                if area == 'basic':
                    plan['enrich_basic_info'] = True
                elif area == 'visual':
                    plan['enrich_visual_assets'] = True
                elif area == 'metadata':
                    plan['enrich_metadata'] = True
                elif area == 'ratings':
                    plan['enrich_ratings'] = True
            return plan

        # Auto-detect what needs enrichment
        if force_refresh or not movie.title_en or not movie.title_vi or not movie.overview_en:
            plan['enrich_basic_info'] = True

        if force_refresh or not movie.poster_url or not movie.backdrop_url:
            plan['enrich_visual_assets'] = True

        if force_refresh or movie.genres.count() == 0 or movie.cast.count() == 0:
            plan['enrich_metadata'] = True

        if force_refresh or not movie.cached_imdb_rating or not movie.cached_tmdb_rating:
            plan['enrich_ratings'] = True

        # Always do additional TMDB enrichment if we have TMDB ID
        if movie.tmdb_id or plan['ensure_tmdb_id']:
            plan['enrich_additional_tmdb'] = True

        return plan

    def _get_current_quality_metrics(self, movie: Movie) -> Dict:
        """Get current quality metrics for a movie"""
        try:
            if hasattr(movie, 'quality_metrics') and movie.quality_metrics:
                return {
                    'quality_score': float(movie.quality_metrics.quality_score or 0),
                    'content_completeness': float(movie.quality_metrics.content_completeness or 0),
                    'minimum_quality_met': movie.quality_metrics.minimum_quality_met,
                    'quality_issues': movie.quality_metrics.quality_issues or [],
                    'quality_suggestions': movie.quality_metrics.quality_suggestions or []
                }
            else:
                # Calculate quality on the fly
                return self.quality_service.calculate_movie_quality(movie, save=False)
        except Exception as e:
            logger.error(f"❌ Error getting quality metrics for movie {movie.id}: {str(e)}")
            return {
                'quality_score': 0,
                'content_completeness': 0,
                'minimum_quality_met': False,
                'quality_issues': [],
                'quality_suggestions': []
            }

    def _map_quality_issues_to_focus_areas(self, quality_issues: List[str]) -> List[str]:
        """
        🎯 Map quality issues to specific focus areas for targeted enrichment
        """
        focus_areas = set()

        for issue in quality_issues:
            issue_lower = issue.lower()

            # Basic information issues
            if any(keyword in issue_lower for keyword in ['title', 'overview', 'release', 'date', 'runtime']):
                focus_areas.add('basic')

            # Visual assets issues
            if any(keyword in issue_lower for keyword in ['poster', 'backdrop', 'image']):
                focus_areas.add('visual')

            # Metadata richness issues
            if any(keyword in issue_lower for keyword in ['cast', 'genre', 'trailer', 'crew', 'keyword']):
                focus_areas.add('metadata')

            # Rating issues
            if any(keyword in issue_lower for keyword in ['rating', 'vote', 'score']):
                focus_areas.add('ratings')

        return list(focus_areas)

    def _calculate_improvements(self, before: Dict, after: Dict) -> List[str]:
        """Calculate improvements made during enrichment"""
        improvements = []

        try:
            # Quality score improvement
            before_score = before.get('quality_score', 0)
            after_score = after.get('quality_score', 0)
            if after_score > before_score:
                improvements.append(f"Quality score: {before_score:.1f} → {after_score:.1f}")

            # Completeness improvement
            before_completeness = before.get('content_completeness', 0)
            after_completeness = after.get('content_completeness', 0)
            if after_completeness > before_completeness:
                improvements.append(f"Completeness: {before_completeness:.1f}% → {after_completeness:.1f}%")

            # Issues resolved
            before_issues = len(before.get('quality_issues', []))
            after_issues = len(after.get('quality_issues', []))
            if after_issues < before_issues:
                improvements.append(f"Issues resolved: {before_issues - after_issues}")

            # Quality threshold met
            if not before.get('minimum_quality_met', False) and after.get('minimum_quality_met', False):
                improvements.append("Minimum quality threshold now met")

        except Exception as e:
            logger.error(f"❌ Error calculating improvements: {str(e)}")

        return improvements

    def _process_movie_chunk(self, movie_ids: List[int], focus_areas: List[str]) -> List[Dict]:
        """Process a chunk of movies for batch enrichment"""
        results = []

        for movie_id in movie_ids:
            try:
                movie = Movie.objects.select_related('quality_metrics').prefetch_related(
                    'genres', 'cast', 'trailers', 'ratings'
                ).get(id=movie_id)

                result = self.enrich_movie_comprehensive(movie, focus_areas=focus_areas)
                results.append(result)

            except Movie.DoesNotExist:
                results.append({
                    'movie_id': movie_id,
                    'success': False,
                    'error': 'Movie not found'
                })
            except Exception as e:
                logger.error(f"❌ Error processing movie {movie_id}: {str(e)}")
                results.append({
                    'movie_id': movie_id,
                    'success': False,
                    'error': str(e)
                })

            # Rate limiting between individual movies
            time.sleep(self.rate_limit_delay)

        return results

    # ===========================================
    # UTILITY AND VALIDATION METHODS
    # ===========================================

    def get_enrichment_status(self, movie: Movie) -> Dict:
        """
        📊 Get comprehensive enrichment status for a movie

        Useful for admin dashboard to show what data is missing/available
        """
        try:
            status = {
                'movie_id': movie.id,
                'movie_title': movie.title,
                'tmdb_id': movie.tmdb_id,
                'imdb_id': movie.imdb_id,
                'data_completeness': {},
                'quality_metrics': {},
                'enrichment_opportunities': []
            }

            # Check data completeness
            status['data_completeness'] = {
                'basic_info': {
                    'title_en': bool(movie.title_en),
                    'title_vi': bool(movie.title_vi),
                    'overview_en': bool(movie.overview_en),
                    'overview_vi': bool(movie.overview_vi),
                    'release_date': bool(movie.release_date),
                    'runtime': bool(movie.runtime),
                    'original_title': bool(movie.original_title)
                },
                'visual_assets': {
                    'poster_url': bool(movie.poster_url),
                    'backdrop_url': bool(movie.backdrop_url),
                    'additional_images': movie.movieimage_set.count() > 0
                },
                'metadata': {
                    'genres': movie.genres.count() > 0,
                    'cast': movie.cast.count() > 0,
                    'trailers': movie.trailers.count() > 0,
                    'has_metadata': hasattr(movie, 'metadata') and movie.metadata is not None
                },
                'ratings': {
                    'cached_imdb_rating': bool(movie.cached_imdb_rating),
                    'cached_tmdb_rating': bool(movie.cached_tmdb_rating),
                    'has_rating_records': movie.ratings.count() > 0
                }
            }

            # Get quality metrics
            status['quality_metrics'] = self._get_current_quality_metrics(movie)

            # Identify enrichment opportunities
            opportunities = []
            if not movie.tmdb_id and movie.imdb_id:
                opportunities.append('Map TMDB ID from IMDB ID')

            if not movie.title_en or not movie.title_vi:
                opportunities.append('Enrich multilingual titles')

            if not movie.overview_en or not movie.overview_vi:
                opportunities.append('Enrich multilingual overviews')

            if not movie.poster_url or not movie.backdrop_url:
                opportunities.append('Enrich visual assets')

            if movie.genres.count() == 0:
                opportunities.append('Add genre information')

            if movie.cast.count() == 0:
                opportunities.append('Add cast and crew')

            if movie.trailers.count() == 0:
                opportunities.append('Add trailer videos')

            status['enrichment_opportunities'] = opportunities

            return status

        except Exception as e:
            logger.error(f"❌ Error getting enrichment status for movie {movie.id}: {str(e)}")
            return {
                'movie_id': movie.id,
                'error': str(e)
            }

    def validate_enrichment_requirements(self, movie: Movie) -> Dict:
        """
        ✅ Validate if a movie can be enriched

        Returns validation results and requirements
        """
        validation = {
            'can_enrich': False,
            'requirements_met': {},
            'blocking_issues': [],
            'recommendations': []
        }

        try:
            # Check basic requirements
            validation['requirements_met']['has_id'] = bool(movie.imdb_id or movie.tmdb_id)
            validation['requirements_met']['has_title'] = bool(movie.title)

            # Check API availability (could be expanded to actual API health checks)
            validation['requirements_met']['tmdb_api'] = True  # Assume available
            validation['requirements_met']['imdb_api'] = True  # Assume available

            # Identify blocking issues
            if not movie.imdb_id and not movie.tmdb_id:
                validation['blocking_issues'].append('No IMDB ID or TMDB ID available')

            if not movie.title:
                validation['blocking_issues'].append('No title available for identification')

            # Generate recommendations
            if movie.imdb_id and not movie.tmdb_id:
                validation['recommendations'].append('Map TMDB ID from IMDB ID for better data access')

            if not movie.title_en and not movie.title_vi:
                validation['recommendations'].append('Enrich with multilingual titles')

            # Determine if enrichment is possible
            validation['can_enrich'] = len(validation['blocking_issues']) == 0

            return validation

        except Exception as e:
            logger.error(f"❌ Error validating enrichment requirements for movie {movie.id}: {str(e)}")
            return {
                'can_enrich': False,
                'error': str(e)
            }
