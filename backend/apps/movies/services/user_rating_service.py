import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.movies.models import Movie, MovieReview
from apps.users.models import UserFavoriteGenre

logger = logging.getLogger(__name__)
User = get_user_model()


class UserRatingService:
    """Service to handle user rating operations and analytics"""

    @staticmethod
    def create_user_rating(user, movie, rating, title=None, content=None, is_public=True, is_spoiler=False):
        """
        Create a new user rating for a movie
        Rating will be normalized to whole numbers (1.0, 2.0, 3.0, 4.0, 5.0)
        """
        try:
            # Normalize rating to whole numbers
            normalized_rating = UserRatingService._normalize_rating(rating)

            with transaction.atomic():
                # Check if user already has a rating for this movie
                existing_review = MovieReview.objects.filter(
                    user=user,
                    movie=movie,
                    review_type='USER'
                ).first()

                if existing_review:
                    # Update existing rating
                    existing_review.rating = normalized_rating
                    if title:
                        existing_review.title = title
                    if content:
                        existing_review.content = content
                    existing_review.is_public = is_public
                    existing_review.is_spoiler = is_spoiler
                    existing_review.updated_at = timezone.now()
                    existing_review.save()
                    return existing_review
                else:
                    # Create new rating
                    review = MovieReview.objects.create(
                        user=user,
                        movie=movie,
                        rating=normalized_rating,
                        title=title or f"Rating for {movie.title}",
                        content=content or f"User rated this movie {normalized_rating}/5 stars",
                        review_type='USER',
                        is_public=is_public,
                        is_spoiler=is_spoiler
                    )
                    return review

        except Exception as e:
            logger.error(f"Error creating user rating: {str(e)}")
            return None

    @staticmethod
    def _normalize_rating(rating):
        """
        Normalize rating to whole numbers (1.0, 2.0, 3.0, 4.0, 5.0)
        Converts any rating scale to 5-point discrete scale
        """
        try:
            rating_float = float(rating)

            #Xử lý thang điểm 5 từ movies lens
            if 0 <= rating_float <= 5:
                if rating_float <= 1.5:
                    return Decimal('1.0')
                elif rating_float <= 2.5:
                    return Decimal('2.0')
                elif rating_float <= 3.5:
                    return Decimal('3.0')
                elif rating_float <= 4.5:
                    return Decimal('4.0')
                else:  # > 4.5
                    return Decimal('5.0')

            # Xử lý thang điểm 10 từ IMDB, TMDB
            elif 0 <= rating_float <= 10:
                # Convert 10-point to 5-point first
                five_point_rating = (rating_float / 10) * 5
                return UserRatingService._normalize_rating(five_point_rating)

            # Xử lý các thang điểm khác (0-100, etc.)
            else:
                normalized = (rating_float / 100) * 5 if rating_float > 10 else rating_float
                return UserRatingService._normalize_rating(normalized)

        except (ValueError, TypeError):
            logger.warning(f"Invalid rating value: {rating}, defaulting to 3.0")
            return Decimal('3.0')

    @staticmethod
    def normalize_external_ratings():
        """
        Normalize all existing external ratings to 5-point discrete scale
        This should be run after importing external datasets
        """
        try:
            # Get all reviews with non-whole number ratings
            reviews_to_normalize = MovieReview.objects.filter(
                review_type='EXTERNAL',
                rating__isnull=False
            ).exclude(
                rating__in=[Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
            )

            normalized_count = 0
            for review in reviews_to_normalize:
                old_rating = review.rating
                new_rating = UserRatingService._normalize_rating(old_rating)

                if old_rating != new_rating:
                    review.rating = new_rating
                    review.save()
                    normalized_count += 1

                    if normalized_count % 1000 == 0:
                        logger.info(f"Normalized {normalized_count} ratings...")

            logger.info(f"Successfully normalized {normalized_count} external ratings")
            return normalized_count

        except Exception as e:
            logger.error(f"Error normalizing external ratings: {str(e)}")
            return 0

    @staticmethod
    def get_user_ratings(user, limit=None):
        """Get all ratings by a user"""
        queryset = MovieReview.objects.filter(
            user=user,
            review_type='USER'
        ).select_related('movie').order_by('-created_at')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def get_movie_user_ratings(movie, limit=None):
        """Get all user ratings for a movie"""
        queryset = MovieReview.objects.filter(
            movie=movie,
            review_type='USER',
            is_public=True
        ).select_related('user').order_by('-created_at')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def calculate_user_rating_stats(user):
        """Calculate rating statistics for a user"""
        user_ratings = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            rating__isnull=False
        )

        if not user_ratings.exists():
            return None

        from django.db import models
        stats = user_ratings.aggregate(
            total_ratings=Count('id'),
            avg_rating=Avg('rating'),
            highest_rating=models.Max('rating'),
            lowest_rating=models.Min('rating')
        )

        # Get rating distribution
        rating_distribution = {}
        for i in range(1, 6):  # 1 to 5 stars
            count = user_ratings.filter(
                rating__gte=i,
                rating__lt=i + 1
            ).count()
            rating_distribution[f"{i}_star"] = count

        # Get favorite genres based on highly rated movies
        favorite_genres = UserFavoriteGenre.objects.filter(user=user)
        if not favorite_genres.exists():
            # Calculate based on ratings
            high_rated_movies = user_ratings.filter(rating__gte=4.0).values_list('movie_id', flat=True)
            favorite_genres_data = Movie.objects.filter(
                id__in=high_rated_movies
            ).values('genres__name').annotate(
                count=Count('genres__name')
            ).order_by('-count')[:5]
        else:
            favorite_genres_data = favorite_genres.values('genre__name')

        return {
            'total_ratings': stats['total_ratings'],
            'average_rating': float(stats['avg_rating']) if stats['avg_rating'] else 0,
            'highest_rating': float(stats['highest_rating']) if stats['highest_rating'] else 0,
            'lowest_rating': float(stats['lowest_rating']) if stats['lowest_rating'] else 0,
            'rating_distribution': rating_distribution,
            'favorite_genres': list(favorite_genres_data),
            'most_recent_rating': user_ratings.first().created_at if user_ratings.exists() else None
        }

    @staticmethod
    def calculate_movie_rating_stats(movie):
        """Calculate user rating statistics for a movie"""
        user_ratings = MovieReview.objects.filter(
            movie=movie,
            review_type='USER',
            rating__isnull=False,
            is_public=True
        )

        if not user_ratings.exists():
            return None

        stats = user_ratings.aggregate(
            total_ratings=Count('id'),
            avg_rating=Avg('rating')
        )

        # Get rating distribution
        rating_distribution = {}
        for i in range(1, 6):  # 1 to 5 stars
            count = user_ratings.filter(
                rating__gte=i,
                rating__lt=i + 1
            ).count()
            rating_distribution[f"{i}_star"] = count

        return {
            'total_user_ratings': stats['total_ratings'],
            'average_user_rating': float(stats['avg_rating']) if stats['avg_rating'] else 0,
            'rating_distribution': rating_distribution,
            'most_recent_rating': user_ratings.first().created_at if user_ratings.exists() else None
        }

    @staticmethod
    def get_user_recommendations_based_on_ratings(user, limit=20):
        """
        Get movie recommendations based on user's rating history
        Simple collaborative filtering approach
        """
        try:
            # Get user's ratings
            user_ratings = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).values_list('movie_id', 'rating')

            if not user_ratings:
                return []

            user_movie_ratings = dict(user_ratings)
            user_avg_rating = sum(user_movie_ratings.values()) / len(user_movie_ratings)

            # Find similar users (users who rated similar movies with similar ratings)
            similar_users = []
            user_rated_movies = set(user_movie_ratings.keys())

            for other_user in User.objects.exclude(id=user.id):
                other_ratings = MovieReview.objects.filter(
                    user=other_user,
                    review_type='USER',
                    rating__isnull=False,
                    movie_id__in=user_rated_movies
                ).values_list('movie_id', 'rating')

                if not other_ratings:
                    continue

                other_movie_ratings = dict(other_ratings)

                # Calculate similarity (simple correlation)
                common_movies = user_rated_movies.intersection(set(other_movie_ratings.keys()))

                if len(common_movies) < 3:  # Need at least 3 common movies
                    continue

                similarity = UserRatingService._calculate_user_similarity(
                    user_movie_ratings, other_movie_ratings, common_movies
                )

                if similarity > 0.5:  # Similarity threshold
                    similar_users.append((other_user, similarity))

            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)
            similar_users = similar_users[:10]  # Top 10 similar users

            # Get movie recommendations from similar users
            recommended_movies = {}

            for similar_user, similarity in similar_users:
                similar_user_ratings = MovieReview.objects.filter(
                    user=similar_user,
                    review_type='USER',
                    rating__gte=4.0,  # Only consider high ratings
                    rating__isnull=False
                ).exclude(
                    movie_id__in=user_rated_movies  # Exclude already rated movies
                ).values_list('movie_id', 'rating')

                for movie_id, rating in similar_user_ratings:
                    if movie_id not in recommended_movies:
                        recommended_movies[movie_id] = []
                    recommended_movies[movie_id].append(float(rating) * similarity)

            # Calculate weighted average ratings
            movie_scores = []
            for movie_id, scores in recommended_movies.items():
                avg_score = sum(scores) / len(scores)
                movie_scores.append((movie_id, avg_score))

            # Sort by score and get top recommendations
            movie_scores.sort(key=lambda x: x[1], reverse=True)
            recommended_movie_ids = [movie_id for movie_id, score in movie_scores[:limit]]

            # Get movie objects
            recommended_movies = Movie.objects.filter(
                id__in=recommended_movie_ids,
                poster_url__isnull=False
            ).select_related().prefetch_related('genres')

            return list(recommended_movies)

        except Exception as e:
            logger.error(f"Error getting user recommendations: {str(e)}")
            return []

    @staticmethod
    def _calculate_user_similarity(user1_ratings, user2_ratings, common_movies):
        """Calculate similarity between two users based on their ratings"""
        if not common_movies:
            return 0

        # Simple Pearson correlation coefficient
        sum1 = sum([user1_ratings[movie] for movie in common_movies])
        sum2 = sum([user2_ratings[movie] for movie in common_movies])

        sum1_sq = sum([user1_ratings[movie] ** 2 for movie in common_movies])
        sum2_sq = sum([user2_ratings[movie] ** 2 for movie in common_movies])

        sum_products = sum([user1_ratings[movie] * user2_ratings[movie] for movie in common_movies])

        n = len(common_movies)
        numerator = sum_products - (sum1 * sum2 / n)
        denominator = ((sum1_sq - sum1 ** 2 / n) * (sum2_sq - sum2 ** 2 / n)) ** 0.5

        if denominator == 0:
            return 0

        correlation = numerator / denominator
        return max(0, correlation)  # Return 0 if negative correlation

    @staticmethod
    def get_trending_movies_by_user_ratings(days=7, limit=20):
        """Get trending movies based on recent user ratings"""
        cutoff_date = timezone.now() - timedelta(days=days)

        trending_movies = Movie.objects.annotate(
            recent_rating_count=Count(
                'reviews',
                filter=Q(
                    reviews__review_type='USER',
                    reviews__created_at__gte=cutoff_date,
                    reviews__rating__gte=4.0
                )
            ),
            avg_recent_rating=Avg(
                'reviews__rating',
                filter=Q(
                    reviews__review_type='USER',
                    reviews__created_at__gte=cutoff_date
                )
            )
        ).filter(
            recent_rating_count__gte=3,  # At least 3 recent ratings
            poster_url__isnull=False
        ).order_by('-recent_rating_count', '-avg_recent_rating')[:limit]

        return trending_movies

    @staticmethod
    def bulk_import_ratings(ratings_data, batch_size=1000):
        """
        Bulk import ratings data

        Args:
            ratings_data: List of dictionaries with keys: user, movie, rating, created_at
            batch_size: Batch size for bulk operations

        Returns:
            Dict with import statistics
        """
        total_processed = 0
        total_created = 0
        total_errors = 0

        # Process in batches
        for i in range(0, len(ratings_data), batch_size):
            batch = ratings_data[i:i + batch_size]

            try:
                with transaction.atomic():
                    reviews_to_create = []

                    for rating_data in batch:
                        try:
                            # Validate data
                            user = rating_data['user']
                            movie = rating_data['movie']
                            rating = Decimal(str(rating_data['rating']))
                            created_at = rating_data.get('created_at', timezone.now())

                            # Check if rating already exists
                            if not MovieReview.objects.filter(
                                user=user,
                                movie=movie,
                                review_type='USER'
                            ).exists():
                                review = MovieReview(
                                    user=user,
                                    movie=movie,
                                    rating=rating,
                                    title=f"Rating for {movie.title}",
                                    content=f"Imported rating: {rating}/5 stars",
                                    review_type='USER',
                                    is_public=True,
                                    created_at=created_at
                                )
                                reviews_to_create.append(review)

                        except Exception as e:
                            logger.error(f"Error preparing rating data: {str(e)}")
                            total_errors += 1
                            continue

                    # Bulk create reviews
                    if reviews_to_create:
                        MovieReview.objects.bulk_create(reviews_to_create, ignore_conflicts=True)
                        total_created += len(reviews_to_create)

                    total_processed += len(batch)

            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                total_errors += len(batch)
                continue

        return {
            'total_processed': total_processed,
            'total_created': total_created,
            'total_errors': total_errors
        }
