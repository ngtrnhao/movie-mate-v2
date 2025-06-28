import logging
import requests
import random
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from bs4 import BeautifulSoup
import json
import time

from ..models import Movie, MovieReview
from apps.users.models import User

logger = logging.getLogger(__name__)

class VietnamMovieReviewService:
    """Service to integrate Vietnamese movie review sources"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    # ==================== BOX OFFICE VIETNAM ====================
    def get_box_office_reviews(self, movie_title: str) -> List[Dict]:
        """Get reviews from Box Office Vietnam"""
        try:
            # Search for movie on Box Office Vietnam
            search_url = "https://boxofficevietnam.com/search"
            params = {'q': movie_title}

            response = requests.get(search_url, params=params, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract movie reviews and ratings
                reviews = []
                # Parse Box Office data and convert to reviews

                return reviews

        except Exception as e:
            logger.error(f"Error fetching Box Office reviews: {e}")
            return []

    # ==================== IMDB VIETNAMESE REVIEWS ====================
    def get_imdb_vietnamese_reviews(self, imdb_id: str) -> List[Dict]:
        """Get Vietnamese reviews from IMDB"""
        try:
            # IMDB API endpoint for reviews with Vietnamese filter
            url = f"https://www.imdb.com/title/{imdb_id}/reviews"
            params = {
                'spoiler': 'hide',
                'sort': 'helpfulnessScore',
                'dir': 'desc',
                'country': 'VN'  # Vietnam filter
            }

            response = requests.get(url, params=params, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                reviews = []
                review_containers = soup.find_all('div', class_='review-container')

                for container in review_containers:
                    # Extract Vietnamese reviews
                    review_text = container.find('div', class_='text')
                    rating_elem = container.find('span', class_='rating-other-user-rating')

                    if review_text and self._is_vietnamese_text(review_text.get_text()):
                        review = {
                            'text': review_text.get_text().strip(),
                            'rating': self._extract_rating(rating_elem),
                            'source': 'IMDB_VN',
                            'language': 'vi'
                        }
                        reviews.append(review)

                return reviews

        except Exception as e:
            logger.error(f"Error fetching IMDB Vietnamese reviews: {e}")
            return []

    # ==================== VIETNAMESE MOVIE SITES ====================
    def get_phimmoi_reviews(self, movie_title: str) -> List[Dict]:
        """Get reviews from Vietnamese movie sites like phimmoi.net"""
        try:
            # Search on Vietnamese movie sites
            search_results = []

            sites = [
                'https://www.phimmoi.net',
                'https://motphim.net',
                'https://bilutv.org'
            ]

            for site in sites:
                reviews = self._scrape_site_reviews(site, movie_title)
                search_results.extend(reviews)

            return search_results

        except Exception as e:
            logger.error(f"Error fetching Vietnamese site reviews: {e}")
            return []

    # ==================== MOVIE REVIEW AGGREGATOR ====================
    def get_aggregated_vietnamese_reviews(self, movie: Movie) -> List[Dict]:
        """Aggregate reviews from all Vietnamese sources"""
        all_reviews = []

        # Get from different sources
        try:
            # Box Office Vietnam
            box_office_reviews = self.get_box_office_reviews(movie.title)
            all_reviews.extend(box_office_reviews)

            # IMDB Vietnamese
            if movie.imdb_id:
                imdb_reviews = self.get_imdb_vietnamese_reviews(movie.imdb_id)
                all_reviews.extend(imdb_reviews)

            # Vietnamese movie sites
            phimmoi_reviews = self.get_phimmoi_reviews(movie.title)
            all_reviews.extend(phimmoi_reviews)

            # Filter and clean reviews
            cleaned_reviews = self._clean_and_filter_reviews(all_reviews)

            return cleaned_reviews

        except Exception as e:
            logger.error(f"Error aggregating Vietnamese reviews: {e}")
            return []

    # ==================== SOCIAL MEDIA REVIEWS ====================
    def get_facebook_reviews(self, movie_title: str) -> List[Dict]:
        """Get reviews from Facebook movie pages (requires API key)"""
        try:
            # Facebook Graph API for movie reviews
            # Note: Requires proper Facebook API credentials

            if not hasattr(settings, 'FACEBOOK_ACCESS_TOKEN'):
                logger.warning("Facebook API credentials not configured")
                return []

            # Search for movie-related posts
            reviews = []
            # Implement Facebook API integration here

            return reviews

        except Exception as e:
            logger.error(f"Error fetching Facebook reviews: {e}")
            return []

    # ==================== IMPORT TO DATABASE ====================
    def import_vietnamese_reviews(self, movie: Movie, limit: int = 50) -> int:
        """Import Vietnamese reviews to database"""
        try:
            # Get aggregated reviews
            reviews_data = self.get_aggregated_vietnamese_reviews(movie)

            if not reviews_data:
                logger.info(f"No Vietnamese reviews found for movie {movie.title}")
                return 0

            # Limit number of reviews
            reviews_data = reviews_data[:limit]

            imported_count = 0

            with transaction.atomic():
                for review_data in reviews_data:
                    # Create or get reviewer user
                    reviewer = self._get_or_create_reviewer(review_data.get('author', 'Anonymous'))

                    # Convert rating to our scale (1-5)
                    rating = self._normalize_rating(review_data.get('rating', 3))

                    # Create review
                    review, created = MovieReview.objects.get_or_create(
                        movie=movie,
                        user=reviewer,
                        defaults={
                            'review_text': review_data.get('text', ''),
                            'rating': Decimal(str(rating)),
                            'review_type': 'EXTERNAL',
                            'source': review_data.get('source', 'VIETNAMESE_SITE'),
                            'language': 'vi',
                            'created_at': timezone.now()
                        }
                    )

                    if created:
                        imported_count += 1
                        logger.info(f"Imported Vietnamese review for {movie.title}")

            # Update movie cached ratings
            self._update_movie_ratings(movie)

            return imported_count

        except Exception as e:
            logger.error(f"Error importing Vietnamese reviews for {movie.title}: {e}")
            return 0

    # ==================== HELPER METHODS ====================
    def _is_vietnamese_text(self, text: str) -> bool:
        """Check if text is in Vietnamese"""
        vietnamese_chars = 'àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêềếểễệđìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ'
        return any(char.lower() in vietnamese_chars for char in text)

    def _extract_rating(self, rating_elem) -> Optional[float]:
        """Extract rating from HTML element"""
        try:
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                # Extract numeric rating
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if match:
                    return float(match.group(1))
            return None
        except:
            return None

    def _scrape_site_reviews(self, site_url: str, movie_title: str) -> List[Dict]:
        """Scrape reviews from Vietnamese movie sites"""
        try:
            # Implement site-specific scraping
            reviews = []

            # Search for movie
            search_url = f"{site_url}/search"
            params = {'q': movie_title}

            response = requests.get(search_url, params=params, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract reviews based on site structure
                # This would need to be customized for each site

            return reviews

        except Exception as e:
            logger.error(f"Error scraping {site_url}: {e}")
            return []

    def _clean_and_filter_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """Clean and filter reviews"""
        cleaned = []

        for review in reviews:
            # Filter out duplicate reviews
            text = review.get('text', '').strip()

            if len(text) < 20:  # Too short
                continue

            if len(text) > 1000:  # Too long, truncate
                text = text[:1000] + "..."
                review['text'] = text

            # Check if Vietnamese
            if not self._is_vietnamese_text(text):
                continue

            cleaned.append(review)

        return cleaned

    def _get_or_create_reviewer(self, author_name: str) -> User:
        """Get or create reviewer user"""
        username = f"reviewer_{author_name.lower().replace(' ', '_')}"[:30]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@external.reviews",
                'first_name': author_name.split()[0] if author_name.split() else 'Anonymous',
                'last_name': ' '.join(author_name.split()[1:]) if len(author_name.split()) > 1 else '',
                'user_type': 'EXTERNAL_REVIEWER'
            }
        )

        return user

    def _normalize_rating(self, rating: Optional[float]) -> float:
        """Normalize rating to 1-5 scale"""
        if rating is None:
            return 3.0

        # Convert different rating scales to 1-5
        if rating <= 1:
            return 1.0
        elif rating <= 5:
            return rating
        elif rating <= 10:
            return rating / 2
        elif rating <= 100:
            return rating / 20
        else:
            return 3.0

    def _update_movie_ratings(self, movie: Movie):
        """Update movie cached ratings"""
        try:
            from django.db import models
            reviews = MovieReview.objects.filter(movie=movie)

            if reviews.exists():
                avg_rating = reviews.aggregate(avg=models.Avg('rating'))['avg']
                total_reviews = reviews.count()

                movie.cached_imdb_rating = avg_rating
                # Note: total_reviews field doesn't exist in model, using comment for tracking
                movie.comment = f"Total reviews: {total_reviews}"
                movie.save(update_fields=['cached_imdb_rating', 'comment'])

        except Exception as e:
            logger.error(f"Error updating movie ratings: {e}")
