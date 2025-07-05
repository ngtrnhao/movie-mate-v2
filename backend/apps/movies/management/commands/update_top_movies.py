from django.core.management.base import BaseCommand
from apps.movies.services.movie_title_genre_service import MovieTitleGenreService
from apps.movies.services.movie_overview_service import MovieOverviewService
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService
from apps.movies.services.tmdb_service import TMDBService
from apps.movies.models import Movie, MovieTrailer
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update title/genre/overview/trailer/backdrop data for movies that appear at the top of movies page'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if data already exists'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of movies to process per category (default: 100)'
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only process movies with missing data'
        )
        parser.add_argument(
            '--skip-overview',
            action='store_true',
            help='Skip overview update (only update title/genre/trailer/backdrop/poster)'
        )
        parser.add_argument(
            '--overview-only',
            action='store_true',
            help='Only update overview (skip title/genre/trailer/backdrop/poster)'
        )
        parser.add_argument(
            '--skip-trailer',
            action='store_true',
            help='Skip trailer update'
        )
        parser.add_argument(
            '--trailer-only',
            action='store_true',
            help='Only update trailer (skip title/genre/overview/backdrop/poster)'
        )
        parser.add_argument(
            '--skip-backdrop',
            action='store_true',
            help='Skip backdrop update'
        )
        parser.add_argument(
            '--backdrop-only',
            action='store_true',
            help='Only update backdrop (skip title/genre/overview/trailer/poster)'
        )
        parser.add_argument(
            '--skip-poster',
            action='store_true',
            help='Skip poster update'
        )
        parser.add_argument(
            '--poster-only',
            action='store_true',
            help='Only update poster (skip title/genre/overview/trailer/backdrop)'
        )
        parser.add_argument(
            '--check-missing-poster',
            action='store_true',
            help='Chỉ kiểm tra/thống kê các phim thiếu poster, không cập nhật'
        )
        parser.add_argument(
            '--update-missing-poster',
            action='store_true',
            help='Cập nhật poster cho toàn bộ movies thiếu poster (không chỉ top movies)'
        )

    def needs_update(self, movie):
        """Check if movie needs title/genre update"""
        missing_title_en = not movie.title_en or movie.title_en.strip() == ''
        missing_title_vi = not movie.title_vi or movie.title_vi.strip() == ''
        missing_genres = movie.genres.count() == 0
        return missing_title_en or missing_title_vi or missing_genres

    def needs_overview_update(self, movie):
        """Check if movie needs overview update"""
        missing_overview_en = not movie.overview_en or movie.overview_en.strip() == ''
        missing_overview_vi = not movie.overview_vi or movie.overview_vi.strip() == ''
        return missing_overview_en or missing_overview_vi

    def needs_trailer_update(self, movie):
        """Check if movie needs trailer update"""
        return not MovieTrailer.objects.filter(movie=movie).exists()

    def needs_backdrop_update(self, movie):
        """Check if movie needs backdrop update"""
        return not movie.backdrop_url or movie.backdrop_url.strip() == ''

    def needs_poster_update(self, movie):
        """Check if movie needs poster update"""
        return not movie.poster_url or movie.poster_url.strip() == ''

    def get_top_movies_by_category(self, limit):
        """Get top movies by different sorting categories"""
        categories = {}

        # 1. Most Popular (is_popular=True)
        popular_movies = Movie.objects.filter(
            is_popular=True,
            imdb_id__isnull=False
        ).order_by('-cached_imdb_rating', '-release_date')[:limit]
        categories['popular'] = popular_movies

        # 2. Highest Rated (by combined_rating_score)
        top_rated_movies = Movie.objects.filter(
            imdb_id__isnull=False,
            combined_rating_score__isnull=False
        ).order_by('-combined_rating_score', '-cached_imdb_rating', '-release_date')[:limit]
        categories['top_rated'] = top_rated_movies

        # 3. Newest (by release_date)
        newest_movies = Movie.objects.filter(
            imdb_id__isnull=False,
            release_date__isnull=False
        ).order_by('-release_date', '-cached_imdb_rating')[:limit]
        categories['newest'] = newest_movies

        # 4. Most Voted (by vote count)
        most_voted_movies = Movie.objects.filter(
            imdb_id__isnull=False,
            cached_imdb_votes__isnull=False
        ).order_by('-cached_imdb_votes', '-cached_imdb_rating', '-release_date')[:limit]
        categories['most_voted'] = most_voted_movies

        # 5. Top Rated by IMDB Rating
        top_imdb_movies = Movie.objects.filter(
            imdb_id__isnull=False,
            cached_imdb_rating__isnull=False
        ).order_by('-cached_imdb_rating', '-cached_imdb_votes', '-release_date')[:limit]
        categories['top_imdb'] = top_imdb_movies

        # 6. Top Rated by TMDB Rating
        top_tmdb_movies = Movie.objects.filter(
            imdb_id__isnull=False,
            cached_tmdb_rating__isnull=False
        ).order_by('-cached_tmdb_rating', '-cached_tmdb_votes', '-release_date')[:limit]
        categories['top_tmdb'] = top_tmdb_movies

        return categories

    def update_movie_overview(self, movie, dry_run=False):
        """Update movie overview from TMDB"""
        try:
            if dry_run:
                return True, "Dry run - no changes made"

            overviews = MovieOverviewService.get_movie_overview(movie.imdb_id, use_cache=False)

            if not overviews:
                return False, "No overviews found"

            # Update movie with new overviews
            update_fields = []
            if "vi" in overviews and overviews["vi"]:
                movie.overview_vi = overviews["vi"]
                update_fields.append('overview_vi')
            if "en" in overviews and overviews["en"]:
                movie.overview_en = overviews["en"]
                update_fields.append('overview_en')

            if update_fields:
                movie.save(update_fields=update_fields)
                return True, f"Updated overviews: {', '.join(update_fields)}"
            else:
                return False, "No valid overviews to update"

        except Exception as e:
            logger.error(f"Error updating overview for movie {movie.imdb_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def update_movie_trailer(self, movie, dry_run=False):
        """Update movie trailer from TMDB"""
        try:
            if dry_run:
                return True, "Dry run - no changes made"

            # Use the existing service to enrich trailers
            MovieTMDBEnrichService.enrich_movie_trailers(movie)

            # Check if trailers were added
            trailer_count = MovieTrailer.objects.filter(movie=movie).count()
            if trailer_count > 0:
                return True, f"Added {trailer_count} trailers"
            else:
                return False, "No trailers found"

        except Exception as e:
            logger.error(f"Error updating trailer for movie {movie.imdb_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def update_movie_backdrop(self, movie, dry_run=False):
        """Update movie backdrop from TMDB"""
        try:
            if dry_run:
                return True, "Dry run - no changes made"

            # Use the existing service to enrich backdrop
            old_backdrop = movie.backdrop_url
            MovieTMDBEnrichService.enrich_backdrop_and_tmdb_id(movie)

            # Refresh movie to get updated data
            movie.refresh_from_db()

            if movie.backdrop_url and movie.backdrop_url != old_backdrop:
                return True, f"Updated backdrop: {movie.backdrop_url[:50]}..."
            else:
                return False, "No backdrop found or already exists"

        except Exception as e:
            logger.error(f"Error updating backdrop for movie {movie.imdb_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def update_movie_poster(self, movie, dry_run=False):
        """Update movie poster from TMDB"""
        try:
            if dry_run:
                return True, "Dry run - no changes made"

            # Get TMDB data
            tmdb_service = TMDBService()
            tmdb_data = tmdb_service.get_movie_details(movie.tmdb_id) if getattr(movie, 'tmdb_id', None) else None

            if not tmdb_data and movie.imdb_id:
                # Try to find TMDB ID from IMDB ID
                find_result = tmdb_service.get_movie_by_imdb_id(movie.imdb_id)
                if find_result and find_result.get("movie_results"):
                    tmdb_id = find_result["movie_results"][0]["id"]
                    movie.tmdb_id = tmdb_id
                    tmdb_data = tmdb_service.get_movie_details(tmdb_id)

            if tmdb_data and tmdb_data.get('poster_path'):
                old_poster = movie.poster_url
                movie.poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_data.get('poster_path')}"
                movie.save(update_fields=['poster_url', 'tmdb_id'])

                if movie.poster_url != old_poster:
                    return True, f"Updated poster: {movie.poster_url[:50]}..."
                else:
                    return False, "Poster already exists"
            else:
                return False, "No poster found in TMDB data"

        except Exception as e:
            logger.error(f"Error updating poster for movie {movie.imdb_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def process_single_movie(self, movie, options):
        """Process a single movie"""
        force = options['force']
        dry_run = options['dry_run']
        skip_overview = options['skip_overview']
        overview_only = options['overview_only']
        skip_trailer = options['skip_trailer']
        trailer_only = options['trailer_only']
        skip_backdrop = options['skip_backdrop']
        backdrop_only = options['backdrop_only']
        skip_poster = options['skip_poster']
        poster_only = options['poster_only']

        # Kiểm tra xem có cần update không
        needs_title_genre_update = self.needs_update(movie)
        needs_overview_update = self.needs_overview_update(movie)
        needs_trailer_update = self.needs_trailer_update(movie)
        needs_backdrop_update = self.needs_backdrop_update(movie)
        needs_poster_update = self.needs_poster_update(movie)

        # Determine what to update based on options
        if overview_only:
            # Chỉ update overview
            if not needs_overview_update and not force:
                return False, "Already has complete overview data"
        elif trailer_only:
            # Chỉ update trailer
            if not needs_trailer_update and not force:
                return False, "Already has trailers"
        elif backdrop_only:
            # Chỉ update backdrop
            if not needs_backdrop_update and not force:
                return False, "Already has backdrop"
        elif poster_only:
            # Chỉ update poster
            if not needs_poster_update and not force:
                return False, "Already has poster"
        else:
            # Update tất cả hoặc theo options
            needs_any_update = (
                (not skip_overview and needs_overview_update) or
                (not skip_trailer and needs_trailer_update) or
                (not skip_backdrop and needs_backdrop_update) or
                (not skip_poster and needs_poster_update) or
                (not any([overview_only, trailer_only, backdrop_only, poster_only]) and needs_title_genre_update)
            )
            if not needs_any_update and not force:
                return False, "Already has complete data"

        # Hiển thị thông tin trước khi update
        self.stdout.write(f"   🎬 {movie.title} (ID: {movie.id})")
        self.stdout.write(f"      IMDB: {movie.imdb_id} | Rating: {movie.cached_imdb_rating or 'N/A'}")

        if not any([overview_only, trailer_only, backdrop_only, poster_only]):
            self.stdout.write(f"      Title EN: {movie.title_en or '❌ Missing'}")
            self.stdout.write(f"      Title VI: {movie.title_vi or '❌ Missing'}")

            genres_en = list(movie.genres.filter(language='en').values_list('name', flat=True))
            genres_vi = list(movie.genres.filter(language='vi').values_list('name', flat=True))

            self.stdout.write(f"      Genres EN: {genres_en or '❌ Missing'}")
            self.stdout.write(f"      Genres VI: {genres_vi or '❌ Missing'}")

        if not skip_overview and not any([trailer_only, backdrop_only, poster_only]):
            self.stdout.write(f"      Overview EN: {movie.overview_en[:50] + '...' if movie.overview_en and len(movie.overview_en) > 50 else movie.overview_en or '❌ Missing'}")
            self.stdout.write(f"      Overview VI: {movie.overview_vi[:50] + '...' if movie.overview_vi and len(movie.overview_vi) > 50 else movie.overview_vi or '❌ Missing'}")

        if not skip_trailer and not any([overview_only, backdrop_only, poster_only]):
            trailer_count = MovieTrailer.objects.filter(movie=movie).count()
            self.stdout.write(f"      Trailers: {trailer_count} found")

        if not skip_backdrop and not any([overview_only, trailer_only, poster_only]):
            self.stdout.write(f"      Backdrop: {movie.backdrop_url or '❌ Missing'}")

        if not skip_poster and not any([overview_only, trailer_only, backdrop_only]):
            self.stdout.write(f"      Poster: {movie.poster_url or '❌ Missing'}")

        if dry_run:
            self.stdout.write("      🔍 DRY RUN - No changes will be made")
            return True, "Dry run completed"

        # Thực hiện sync
        success_messages = []

        # Update title/genre nếu cần
        if not any([overview_only, trailer_only, backdrop_only, poster_only]) and (needs_title_genre_update or force):
            self.stdout.write("      🔄 Syncing title/genre from TMDB...")
            success, message = MovieTitleGenreService.sync_movie_data(movie, use_cache=False)
            if success:
                success_messages.append("Title/genre sync successful")
            else:
                self.stdout.write(f"      ❌ Title/genre sync failed: {message}")

        # Update overview nếu cần
        if not skip_overview and not any([trailer_only, backdrop_only, poster_only]) and (needs_overview_update or force):
            self.stdout.write("      🔄 Syncing overview from TMDB...")
            success, message = self.update_movie_overview(movie, dry_run=False)
            if success:
                success_messages.append("Overview sync successful")
            else:
                self.stdout.write(f"      ❌ Overview sync failed: {message}")

        # Update trailer nếu cần
        if not skip_trailer and not any([overview_only, backdrop_only, poster_only]) and (needs_trailer_update or force):
            self.stdout.write("      🔄 Syncing trailer from TMDB...")
            success, message = self.update_movie_trailer(movie, dry_run=False)
            if success:
                success_messages.append("Trailer sync successful")
            else:
                self.stdout.write(f"      ❌ Trailer sync failed: {message}")

        # Update backdrop nếu cần
        if not skip_backdrop and not any([overview_only, trailer_only, poster_only]) and (needs_backdrop_update or force):
            self.stdout.write("      🔄 Syncing backdrop from TMDB...")
            success, message = self.update_movie_backdrop(movie, dry_run=False)
            if success:
                success_messages.append("Backdrop sync successful")
            else:
                self.stdout.write(f"      ❌ Backdrop sync failed: {message}")

        # Update poster nếu cần
        if not skip_poster and not any([overview_only, trailer_only, backdrop_only]) and (needs_poster_update or force):
            self.stdout.write("      🔄 Syncing poster from TMDB...")
            success, message = self.update_movie_poster(movie, dry_run=False)
            if success:
                success_messages.append("Poster sync successful")
            else:
                self.stdout.write(f"      ❌ Poster sync failed: {message}")

        if success_messages:
            # Refresh movie object để lấy data mới
            movie.refresh_from_db()

            self.stdout.write("      ✅ " + " | ".join(success_messages))
            return True, " | ".join(success_messages)
        else:
            return False, "All sync operations failed"

    def handle(self, *args, **options):
        limit = options['limit']
        missing_only = options['missing_only']
        skip_overview = options['skip_overview']
        overview_only = options['overview_only']
        skip_trailer = options['skip_trailer']
        trailer_only = options['trailer_only']
        skip_backdrop = options['skip_backdrop']
        backdrop_only = options['backdrop_only']
        skip_poster = options['skip_poster']
        poster_only = options['poster_only']
        check_missing_poster = options.get('check_missing_poster', False)
        update_missing_poster = options.get('update_missing_poster', False)

        if check_missing_poster:
            total = Movie.objects.count()
            missing_qs = Movie.objects.filter(poster_url__isnull=True) | Movie.objects.filter(poster_url__exact='')
            missing_count = missing_qs.count()
            percent = (missing_count / total) * 100 if total > 0 else 0
            self.stdout.write(f"\n❌ Movies missing poster: {missing_count:,} / {total:,} ({percent:.1f}%)")
            self.stdout.write(f"🔍 Sample movies without poster:")
            for movie in missing_qs[:5]:
                self.stdout.write(f"   - ID: {movie.id}, Title: {movie.title}")
            return

        if update_missing_poster:
            total = Movie.objects.count()
            missing_qs = Movie.objects.filter(poster_url__isnull=True) | Movie.objects.filter(poster_url__exact='')
            missing_count = missing_qs.count()
            percent = (missing_count / total) * 100 if total > 0 else 0
            self.stdout.write(f"\n🚀 Updating poster for {missing_count:,} movies missing poster out of {total:,} ({percent:.1f}%)")
            success_count = 0
            error_count = 0
            for i, movie in enumerate(missing_qs.iterator(), 1):
                try:
                    success, message = self.update_movie_poster(movie, dry_run=False)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                    if i % 100 == 0 or i == missing_count:
                        self.stdout.write(f"   Progress: {i}/{missing_count} ({i/missing_count*100:.1f}%)")
                except Exception as e:
                    self.stdout.write(f"   💥 Error updating poster for movie {movie.id}: {str(e)}")
                    error_count += 1
            self.stdout.write(f"\n✅ Poster update completed!")
            self.stdout.write(f"   Successful: {success_count}")
            self.stdout.write(f"   Errors: {error_count}")
            if missing_count > 0:
                self.stdout.write(f"   Success rate: {success_count/missing_count*100:.1f}%")
            return

        self.stdout.write("🎯 Updating top movies from movies page...")
        self.stdout.write(f"📊 Processing top {limit} movies per category")

        # Determine mode
        if overview_only:
            self.stdout.write("📝 Mode: Overview only")
        elif trailer_only:
            self.stdout.write("📝 Mode: Trailer only")
        elif backdrop_only:
            self.stdout.write("📝 Mode: Backdrop only")
        elif poster_only:
            self.stdout.write("📝 Mode: Poster only")
        elif skip_overview and skip_trailer and skip_backdrop and skip_poster:
            self.stdout.write("📝 Mode: Title/Genre only")
        elif skip_overview and skip_trailer and skip_backdrop:
            self.stdout.write("📝 Mode: Title/Genre + Overview + Poster")
        elif skip_overview and skip_trailer and skip_poster:
            self.stdout.write("📝 Mode: Title/Genre + Overview + Backdrop")
        elif skip_overview and skip_backdrop and skip_poster:
            self.stdout.write("📝 Mode: Title/Genre + Overview + Trailer")
        elif skip_trailer and skip_backdrop and skip_poster:
            self.stdout.write("📝 Mode: Title/Genre + Overview")
        else:
            self.stdout.write("📝 Mode: All data (Title/Genre + Overview + Trailer + Backdrop + Poster)")

        # Lấy top movies theo từng category
        categories = self.get_top_movies_by_category(limit)

        # Thống kê tổng quan
        total_movies = 0
        for category, movies in categories.items():
            if missing_only:
                if overview_only:
                    filtered_movies = [m for m in movies if self.needs_overview_update(m)]
                elif trailer_only:
                    filtered_movies = [m for m in movies if self.needs_trailer_update(m)]
                elif backdrop_only:
                    filtered_movies = [m for m in movies if self.needs_backdrop_update(m)]
                elif poster_only:
                    filtered_movies = [m for m in movies if self.needs_poster_update(m)]
                else:
                    filtered_movies = [m for m in movies if (
                        self.needs_update(m) or
                        self.needs_overview_update(m) or
                        self.needs_trailer_update(m) or
                        self.needs_backdrop_update(m) or
                        self.needs_poster_update(m)
                    )]
            else:
                filtered_movies = list(movies)
            total_movies += len(filtered_movies)

            self.stdout.write(f"   📈 {category.replace('_', ' ').title()}: {len(filtered_movies)} movies")

        if total_movies == 0:
            self.stdout.write(self.style.WARNING("⚠️  No movies found to process"))
            return

        # Process từng category
        overall_success_count = 0
        overall_error_count = 0

        for category, movies in categories.items():
            if missing_only:
                if overview_only:
                    filtered_movies = [m for m in movies if self.needs_overview_update(m)]
                elif trailer_only:
                    filtered_movies = [m for m in movies if self.needs_trailer_update(m)]
                elif backdrop_only:
                    filtered_movies = [m for m in movies if self.needs_backdrop_update(m)]
                elif poster_only:
                    filtered_movies = [m for m in movies if self.needs_poster_update(m)]
                else:
                    filtered_movies = [m for m in movies if (
                        self.needs_update(m) or
                        self.needs_overview_update(m) or
                        self.needs_trailer_update(m) or
                        self.needs_backdrop_update(m) or
                        self.needs_poster_update(m)
                    )]
            else:
                filtered_movies = list(movies)

            if not filtered_movies:
                continue

            self.stdout.write(f"\n🌟 Processing {category.replace('_', ' ').title()} movies:")
            self.stdout.write("=" * 60)

            success_count = 0
            error_count = 0

            for i, movie in enumerate(filtered_movies, 1):
                try:
                    success, message = self.process_single_movie(movie, options)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1

                    # Progress indicator
                    if i % 10 == 0 or i == len(filtered_movies):
                        self.stdout.write(f"      📈 Progress: {i}/{len(filtered_movies)} ({i/len(filtered_movies)*100:.1f}%)")

                except Exception as e:
                    self.stdout.write(f"      💥 Error processing movie {movie.id}: {str(e)}")
                    error_count += 1
                    continue

            overall_success_count += success_count
            overall_error_count += error_count

            self.stdout.write(f"\n📊 {category.replace('_', ' ').title()} Summary:")
            self.stdout.write(f"   Successful: {success_count}")
            self.stdout.write(f"   Errors: {error_count}")
            if len(filtered_movies) > 0:
                self.stdout.write(f"   Success rate: {success_count/len(filtered_movies)*100:.1f}%")

        # Final summary
        self.stdout.write(f"\n🎉 OVERALL PROCESSING COMPLETED!")
        self.stdout.write(f"📊 Overall Summary:")
        self.stdout.write(f"   Total processed: {total_movies}")
        self.stdout.write(f"   Successful: {overall_success_count}")
        self.stdout.write(f"   Errors: {overall_error_count}")
        if total_movies > 0:
            self.stdout.write(f"   Success rate: {overall_success_count/total_movies*100:.1f}%")

        self.stdout.write(f"\n💡 Categories processed:")
        for category in categories.keys():
            self.stdout.write(f"   • {category.replace('_', ' ').title()}")
