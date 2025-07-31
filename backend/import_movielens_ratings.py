#!/usr/bin/env python
"""
Import MovieLens ratings và reviews tối ưu cho Collaborative Filtering và Demographic Filtering
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

def import_movielens_ratings():
    """Import MovieLens ratings từ dataset"""
    print("📥 IMPORTING MOVIELENS RATINGS")
    print("=" * 50)
    
    # Đường dẫn đến MovieLens dataset
    dataset_path = "data/movielens/ml-latest-small"
    ratings_file = os.path.join(dataset_path, "ratings.csv")
    
    if not os.path.exists(ratings_file):
        print(f"❌ MovieLens dataset not found at: {ratings_file}")
        print("   Please download MovieLens dataset first")
        return
    
    print(f"📂 Reading ratings from: {ratings_file}")
    
    # Đọc ratings
    ratings_created = 0
    ratings_skipped = 0
    users_created = 0
    
    with open(ratings_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                user_id = int(row['userId'])
                movie_id = int(row['movieId'])
                rating = float(row['rating'])
                timestamp = row['timestamp']
                
                # Tạo hoặc lấy user
                username = f"ml_user_{user_id}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f"{username}@movielens.com",
                        'first_name': f'ML',
                        'last_name': f'User{user_id}',
                        'is_active': True
                    }
                )
                
                if created:
                    users_created += 1
                
                # Tìm movie trong database
                movie = Movie.objects.filter(id=movie_id).first()
                if not movie:
                    ratings_skipped += 1
                    continue
                
                # Kiểm tra rating đã tồn tại
                existing_rating = MovieReview.objects.filter(
                    user=user,
                    movie=movie,
                    review_type='USER'
                ).first()
                
                if not existing_rating:
                    # Tạo rating với review text
                    review_text = f"MovieLens rating: {rating}/5 stars"
                    if rating >= 4.0:
                        review_text += " - Great movie!"
                    elif rating >= 3.0:
                        review_text += " - Good movie"
                    elif rating >= 2.0:
                        review_text += " - Average movie"
                    else:
                        review_text += " - Not recommended"
                    
                    MovieReview.objects.create(
                        user=user,
                        movie=movie,
                        rating=rating,
                        content=review_text,
                        review_type='USER',
                        is_approved=True
                    )
                    ratings_created += 1
                else:
                    ratings_skipped += 1
                    
            except (ValueError, KeyError) as e:
                ratings_skipped += 1
                continue
    
    print(f"✅ Import completed:")
    print(f"   👥 Users created: {users_created}")
    print(f"   ⭐ Ratings created: {ratings_created}")
    print(f"   ⏭️ Ratings skipped: {ratings_skipped}")

def create_demographic_clusters():
    """Tạo demographic clusters cho DF"""
    print("👥 CREATING DEMOGRAPHIC CLUSTERS FOR DF")
    print("=" * 50)
    
    # Tạo các demographic clusters cơ bản
    demographics = [
        {'name': 'Young Students', 'age_range_min': 18, 'age_range_max': 25, 'primary_gender': 'M', 'common_occupations': ['student'], 'preferred_genres': ['Action', 'Comedy']},
        {'name': 'Young Students F', 'age_range_min': 18, 'age_range_max': 25, 'primary_gender': 'F', 'common_occupations': ['student'], 'preferred_genres': ['Romance', 'Drama']},
        {'name': 'Young Professionals', 'age_range_min': 26, 'age_range_max': 35, 'primary_gender': 'M', 'common_occupations': ['engineer', 'manager'], 'preferred_genres': ['Action', 'Thriller']},
        {'name': 'Young Professionals F', 'age_range_min': 26, 'age_range_max': 35, 'primary_gender': 'F', 'common_occupations': ['teacher', 'manager'], 'preferred_genres': ['Drama', 'Romance']},
        {'name': 'Middle Aged', 'age_range_min': 36, 'age_range_max': 50, 'primary_gender': 'M', 'common_occupations': ['manager', 'engineer'], 'preferred_genres': ['Drama', 'Action']},
        {'name': 'Middle Aged F', 'age_range_min': 36, 'age_range_max': 50, 'primary_gender': 'F', 'common_occupations': ['teacher', 'artist'], 'preferred_genres': ['Drama', 'Comedy']},
        {'name': 'Seniors', 'age_range_min': 51, 'age_range_max': 65, 'primary_gender': 'M', 'common_occupations': ['retired'], 'preferred_genres': ['Drama', 'Biography']},
        {'name': 'Seniors F', 'age_range_min': 51, 'age_range_max': 65, 'primary_gender': 'F', 'common_occupations': ['retired'], 'preferred_genres': ['Drama', 'Romance']},
    ]
    
    clusters_created = 0
    for demo in demographics:
        cluster, created = DemographicCluster.objects.get_or_create(
            name=demo['name'],
            defaults=demo
        )
        if created:
            clusters_created += 1
    
    print(f"✅ Created {clusters_created} demographic clusters")

def assign_users_to_clusters():
    """Gán MovieLens users vào demographic clusters"""
    print("🔗 ASSIGNING USERS TO DEMOGRAPHIC CLUSTERS")
    print("=" * 50)
    
    # Lấy tất cả MovieLens users
    ml_users = User.objects.filter(username__startswith='ml_user_')
    clusters = DemographicCluster.objects.all()
    
    if not clusters.exists():
        print("❌ No demographic clusters found. Creating clusters first...")
        create_demographic_clusters()
        clusters = DemographicCluster.objects.all()
    
    preferences_created = 0
    for user in ml_users:
        # Gán random cluster cho mỗi user
        cluster = random.choice(clusters)
        
        # Tạo user preference
        preference, created = UserPreference.objects.get_or_create(
            user=user,
            defaults={
                'demographic_cluster': cluster,
                'preferred_genres': cluster.preferred_genres,
                'preferred_languages': ['en'],
                'preferred_years': [random.randint(1990, 2020)],
                'rating_threshold': random.uniform(3.0, 4.5)
            }
        )
        
        if created:
            preferences_created += 1
    
    print(f"✅ Created {preferences_created} user preferences")

def compute_similarity_matrices():
    """Tính toán similarity matrices"""
    print("🔗 COMPUTING SIMILARITY MATRICES")
    print("=" * 50)
    
    try:
        from django.core.management import call_command
        call_command('compute_similarity_matrices',
                    '--max-users', '200',
                    '--batch-size', '20',
                    '--min-ratings', '5',
                    '--similarity-threshold', '0.2')
        print("✅ Similarity matrices computed successfully")
    except Exception as e:
        print(f"❌ Error computing similarities: {str(e)}")

def generate_recommendations():
    """Tạo recommendations cho MovieLens users"""
    print("💡 GENERATING RECOMMENDATIONS")
    print("=" * 50)
    
    from apps.recommendations.services import (
        CollaborativeFilteringService,
        DemographicFilteringService
    )
    
    # Lấy MovieLens users có ratings
    users = User.objects.filter(
        username__startswith='ml_user_',
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct()[:50]  # Test với 50 users
    
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

def show_results():
    """Hiển thị kết quả import"""
    print("📊 IMPORT RESULTS")
    print("=" * 50)
    
    total_users = User.objects.filter(username__startswith='ml_user_').count()
    total_ratings = MovieReview.objects.filter(
        user__username__startswith='ml_user_',
        review_type='USER'
    ).count()
    total_similarities = UserSimilarity.objects.filter(similarity_type='collaborative').count()
    total_recommendations = RecommendationResult.objects.filter(
        recommendation_type__in=['collaborative', 'demographic']
    ).count()
    total_clusters = DemographicCluster.objects.count()
    total_preferences = UserPreference.objects.count()
    
    print(f"👥 MovieLens users: {total_users}")
    print(f"⭐ MovieLens ratings: {total_ratings}")
    print(f"🔗 Similarities: {total_similarities}")
    print(f"💡 Recommendations: {total_recommendations}")
    print(f"👥 Demographic clusters: {total_clusters}")
    print(f"⚙️ User preferences: {total_preferences}")

def main():
    """Main function"""
    print("🚀 MOVIELENS RATINGS IMPORT FOR CF AND DF")
    print("=" * 60)
    
    # 1. Import MovieLens ratings
    import_movielens_ratings()
    
    # 2. Create demographic clusters
    create_demographic_clusters()
    
    # 3. Assign users to clusters
    assign_users_to_clusters()
    
    # 4. Compute similarities
    compute_similarity_matrices()
    
    # 5. Generate recommendations
    generate_recommendations()
    
    # 6. Show results
    show_results()
    
    print(f"\n✅ MovieLens import completed successfully!")
    print(f"🚀 CF and DF are now ready for testing")

if __name__ == "__main__":
    main()