#!/usr/bin/env python3
"""
Create ratings for test user to enable CF
"""
import os
import sys
import django
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.movies.models import Movie, MovieReview

User = get_user_model()

def create_ratings_for_test_user():
    print("🎬 CREATING RATINGS FOR TEST USER")
    print("=" * 40)
    
    # Get test user
    test_user = User.objects.get(username="testuser_cf")
    print(f"Test user: {test_user.username} (ID: {test_user.id})")
    
    # Get some movies
    movies = list(Movie.objects.all()[:20])
    print(f"Using {len(movies)} movies")
    
    # Get existing users with ratings for similarity
    existing_users = list(User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct()[:5])
    
    print(f"Found {len(existing_users)} existing users with ratings")
    
    ratings_created = 0
    
    # Create ratings for test user
    print("\n📝 Creating ratings for test user...")
    
    # Rate 10 movies
    for movie in movies[:10]:
        rating = random.randint(1, 5)
        
        MovieReview.objects.create(
            user=test_user,
            movie=movie,
            rating=Decimal(str(rating)),
            review_type='USER',
            created_at=timezone.now()
        )
        ratings_created += 1
        print(f"  Rated {movie.title}: {rating}/5")
    
    # Create overlapping ratings with existing users
    print("\n🔗 Creating overlapping ratings...")
    
    # Get movies that existing users have rated
    common_movies = Movie.objects.filter(
        reviews__user__in=existing_users,
        reviews__review_type='USER',
        reviews__rating__isnull=False
    ).distinct()[:5]
    
    for movie in common_movies:
        # Rate the same movies as existing users
        rating = random.randint(1, 5)
        
        existing_rating = MovieReview.objects.filter(
            user=test_user,
            movie=movie,
            review_type='USER'
        ).first()
        
        if not existing_rating:
            MovieReview.objects.create(
                user=test_user,
                movie=movie,
                rating=Decimal(str(rating)),
                review_type='USER',
                created_at=timezone.now()
            )
            ratings_created += 1
            print(f"  Rated common movie {movie.title}: {rating}/5")
    
    print(f"\n✅ Created {ratings_created} ratings for test user")
    
    # Test CF with test user
    print("\n🧪 Testing CF with test user...")
    from apps.recommendations.services import CollaborativeFilteringService
    
    cf_service = CollaborativeFilteringService()
    cf_service.min_common_ratings = 2
    cf_service.similarity_threshold = 0.01
    
    # Find similar users
    similar_users = cf_service.find_similar_users(test_user, limit=5)
    print(f"Similar users found: {len(similar_users)}")
    
    if similar_users:
        for user, similarity in similar_users:
            print(f"  - {user.username}: {similarity:.4f}")
    
    # Generate recommendations
    recommendations = cf_service.generate_collaborative_recommendations(test_user, limit=5)
    print(f"CF recommendations: {len(recommendations)}")
    
    if recommendations:
        print("Recommended movies:")
        for movie in recommendations:
            print(f"  - {movie.title}")
    
    print(f"\n✅ Test user is ready for frontend testing!")
    print(f"🔑 Login: testuser_cf / testpass123")

if __name__ == "__main__":
    create_ratings_for_test_user()