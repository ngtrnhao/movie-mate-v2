#!/usr/bin/env python
"""
Import dữ liệu tối ưu cho Collaborative Filtering và Demographic Filtering
"""
import os
import sys
import django
import csv
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserSimilarity, RecommendationResult, UserPreference, DemographicCluster

User = get_user_model()

def cleanup_old_data():
    """Xóa dữ liệu cũ để chuẩn bị import mới"""
    print("🧹 Cleaning up old data...")
    
    # Xóa old similarities
    old_similarities = UserSimilarity.objects.filter(
        similarity_type='collaborative'
    ).count()
    UserSimilarity.objects.filter(similarity_type='collaborative').delete()
    print(f"   🗑️ Deleted {old_similarities} old similarities")
    
    # Xóa old CF recommendations
    old_recommendations = RecommendationResult.objects.filter(
        recommendation_type='collaborative'
    ).count()
    RecommendationResult.objects.filter(recommendation_type='collaborative').delete()
    print(f"   🗑️ Deleted {old_recommendations} old CF recommendations")
    
    # Xóa old MovieLens ratings
    old_ratings = MovieReview.objects.filter(
        user__username__startswith='ml_user_',
        review_type='USER'
    ).count()
    MovieReview.objects.filter(
        user__username__startswith='ml_user_',
        review_type='USER'
    ).delete()
    print(f"   🗑️ Deleted {old_ratings} old MovieLens ratings")

def create_optimized_users(num_users=500):
    """Tạo users tối ưu cho CF và DF"""
    print(f"👥 Creating {num_users} optimized users...")
    
    # Tạo users với demographics đa dạng
    age_groups = ['18-25', '26-35', '36-45', '46-55', '55+']
    genders = ['M', 'F']
    occupations = ['student', 'engineer', 'teacher', 'manager', 'artist']
    
    created_users = []
    for i in range(1, num_users + 1):
        username = f"cf_user_{i}"
        email = f"cf_user_{i}@example.com"
        
        # Tạo user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': f'CF',
                'last_name': f'User{i}',
                'is_active': True
            }
        )
        
        if created:
            # Tạo user preferences cho DF
            age_group = random.choice(age_groups)
            gender = random.choice(genders)
            occupation = random.choice(occupations)
            
            # Tìm hoặc tạo demographic cluster
            cluster, _ = DemographicCluster.objects.get_or_create(
                age_group=age_group,
                gender=gender,
                occupation=occupation,
                defaults={
                    'cluster_name': f"{age_group}_{gender}_{occupation}",
                    'description': f"Cluster for {age_group} {gender} {occupation}"
                }
            )
            
            # Tạo user preference
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    'demographic_cluster': cluster,
                    'preferred_genres': random.sample(['Action', 'Drama', 'Comedy', 'Thriller'], 2),
                    'preferred_languages': ['en'],
                    'preferred_years': [random.randint(1990, 2020)],
                    'rating_threshold': random.uniform(3.0, 4.5)
                }
            )
            
            created_users.append(user)
    
    print(f"✅ Created {len(created_users)} optimized users with demographics")
    return created_users

def generate_optimized_ratings(num_ratings=10000):
    """Tạo ratings tối ưu cho CF"""
    print(f"⭐ Generating {num_ratings} optimized ratings...")
    
    # Lấy users và movies
    users = User.objects.filter(username__startswith='cf_user_')
    movies = Movie.objects.filter(
        is_published=True,
        vote_average__gte=5.0  # Chỉ lấy movies có rating tốt
    )[:500]  # Giới hạn 500 movies chất lượng
    
    if not users.exists():
        print("❌ No optimized users found. Creating users first...")
        create_optimized_users(100)
        users = User.objects.filter(username__startswith='cf_user_')
    
    if not movies.exists():
        print("❌ No quality movies found")
        return
    
    print(f"   📊 Users: {users.count()}")
    print(f"   🎬 Quality movies: {movies.count()}")
    
    # Tạo ratings với pattern thực tế
    ratings_created = 0
    
    # Tạo overlapping ratings để CF hoạt động tốt
    popular_movies = list(movies.order_by('-vote_average')[:50])  # Top 50 movies
    
    for user in users:
        # Mỗi user rate ít nhất 10 movies
        user_ratings = random.randint(10, 30)
        
        # Đảm bảo có overlap với popular movies
        overlap_count = random.randint(3, 8)
        overlap_movies = random.sample(popular_movies, overlap_count)
        
        for movie in overlap_movies:
            # Rating dựa trên movie quality
            base_rating = movie.vote_average / 2  # Convert từ 10-scale sang 5-scale
            rating = max(1, min(5, base_rating + random.uniform(-1, 1)))
            
            MovieReview.objects.get_or_create(
                user=user,
                movie=movie,
                review_type='USER',
                defaults={
                    'rating': round(rating, 1),
                    'review_text': f"Generated rating for {movie.title}",
                    'is_approved': True
                }
            )
            ratings_created += 1
        
        # Rate thêm random movies
        remaining_ratings = user_ratings - overlap_count
        random_movies = random.sample(list(movies), remaining_ratings)
        
        for movie in random_movies:
            if movie not in overlap_movies:
                base_rating = movie.vote_average / 2
                rating = max(1, min(5, base_rating + random.uniform(-1, 1)))
                
                MovieReview.objects.get_or_create(
                    user=user,
                    movie=movie,
                    review_type='USER',
                    defaults={
                        'rating': round(rating, 1),
                        'review_text': f"Generated rating for {movie.title}",
                        'is_approved': True
                    }
                )
                ratings_created += 1
    
    print(f"✅ Created {ratings_created} optimized ratings with overlap")

def compute_similarity_matrices():
    """Tính toán similarity matrices"""
    print("🔗 Computing similarity matrices...")
    
    try:
        from django.core.management import call_command
        call_command('compute_similarity_matrices', 
                    '--max-users', '100',
                    '--batch-size', '20',
                    '--min-ratings', '5',
                    '--similarity-threshold', '0.2')
        print("✅ Similarity matrices computed successfully")
    except Exception as e:
        print(f"❌ Error computing similarities: {str(e)}")

def generate_recommendations():
    """Tạo recommendations cho tất cả users"""
    print("💡 Generating recommendations...")
    
    from apps.recommendations.services import (
        CollaborativeFilteringService,
        DemographicFilteringService
    )
    
    users = User.objects.filter(username__startswith='cf_user_')[:50]  # Test với 50 users
    
    cf_service = CollaborativeFilteringService()
    df_service = DemographicFilteringService()
    
    cf_count = 0
    df_count = 0
    
    for user in users:
        try:
            # Generate CF recommendations
            cf_recommendations = cf_service.generate_collaborative_recommendations(user, limit=10)
            if cf_recommendations:
                cf_count += 1
            
            # Generate DF recommendations
            df_recommendations = df_service.generate_demographic_recommendations(user, limit=10)
            if df_recommendations:
                df_count += 1
                
        except Exception as e:
            print(f"⚠️ Error generating recommendations for {user.username}: {str(e)}")
    
    print(f"✅ Generated recommendations for {cf_count} users (CF) and {df_count} users (DF)")

def main():
    """Main function"""
    print("🚀 OPTIMIZED DATA IMPORT FOR CF AND DF")
    print("=" * 60)
    
    # 1. Cleanup old data
    cleanup_old_data()
    
    # 2. Import options
    print(f"\n📥 IMPORT OPTIONS:")
    print("   1. Quick test (100 users, 2000 ratings)")
    print("   2. Medium scale (500 users, 10000 ratings)")
    print("   3. Large scale (1000 users, 20000 ratings)")
    
    choice = input("Enter choice (1-3, default 1): ").strip() or "1"
    
    if choice == "1":
        num_users = 100
        num_ratings = 2000
    elif choice == "2":
        num_users = 500
        num_ratings = 10000
    elif choice == "3":
        num_users = 1000
        num_ratings = 20000
    else:
        num_users = 100
        num_ratings = 2000
    
    # 3. Create optimized users
    create_optimized_users(num_users)
    
    # 4. Generate optimized ratings
    generate_optimized_ratings(num_ratings)
    
    # 5. Compute similarities
    compute_similarity_matrices()
    
    # 6. Generate recommendations
    generate_recommendations()
    
    # 7. Show results
    print(f"\n📊 IMPORT RESULTS:")
    total_users = User.objects.filter(username__startswith='cf_user_').count()
    total_ratings = MovieReview.objects.filter(
        user__username__startswith='cf_user_',
        review_type='USER'
    ).count()
    total_similarities = UserSimilarity.objects.filter(similarity_type='collaborative').count()
    total_recommendations = RecommendationResult.objects.filter(
        recommendation_type__in=['collaborative', 'demographic']
    ).count()
    
    print(f"   👥 Optimized users: {total_users}")
    print(f"   ⭐ Optimized ratings: {total_ratings}")
    print(f"   🔗 Similarities: {total_similarities}")
    print(f"   💡 Recommendations: {total_recommendations}")
    
    print(f"\n✅ Import completed successfully!")
    print(f"🚀 CF and DF are now ready for testing")

if __name__ == "__main__":
    main()