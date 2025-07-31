#!/usr/bin/env python
"""
Demo: In ra toàn bộ pipeline Demographic Filtering cho 1 user thực tế
"""

import os
import django
import numpy as np

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.users.models import User
from apps.recommendations.models import UserPreference, DemographicCluster
from apps.recommendations.services import AdvancedDemographicVectorizer, EnhancedDemographicFilteringService

def get_full_user():
    # Lấy user có đủ age, gender, occupation, location, user_type và có rating
    user = (
        User.objects.filter(
            age__isnull=False,
            gender__isnull=False,
            occupation__isnull=False,
            location__isnull=False,
            user_type__isnull=False
        )
        .order_by('-id')
        .first()
    )
    return user

def print_vector(name, vector, feature_names=None):
    print(f"\n{name}:")
    if feature_names:
        for i, v in enumerate(vector):
            print(f"  {feature_names[i]}: {v}")
    else:
        print(vector)

def main():
    user = get_full_user()
    if not user:
        print("Không tìm thấy user đủ thông tin.")
        return

    print("=== THÔNG TIN GỐC USER ===")
    print(f"ID: {user.id}, Age: {user.age}, Gender: {user.gender}, Occupation: {user.occupation}, Location: {user.location}, User type: {user.user_type}")

    # 1. Vector hóa demographics (one-hot)
    vectorizer = AdvancedDemographicVectorizer()
    demo_vector = vectorizer.create_demographic_vector(user)
    feature_names = vectorizer.get_feature_names() if hasattr(vectorizer, "get_feature_names") else [f"f{i}" for i in range(len(demo_vector))]
    print_vector("Demographic vector (one-hot)", demo_vector, feature_names)

    # 2. Vector hóa hành vi
    user_pref = UserPreference.objects.filter(user=user).first()
    if user_pref and hasattr(user_pref, "behavioral_vector") and user_pref.behavioral_vector:
        behavioral_vector = np.array(user_pref.behavioral_vector)
        print_vector("Behavioral vector", behavioral_vector)
    else:
        print("\nBehavioral vector: Không có dữ liệu.")

    # 3. Phân cụm K-means
    filtering_service = EnhancedDemographicFilteringService()
    cluster = filtering_service.get_user_kmeans_cluster(user)
    if cluster:
        print(f"\nUser được gán vào K-means cluster: {cluster.cluster_id} - {cluster.name}")
        # In centroid_vector nếu có, nếu không thì in các trường khác
        if hasattr(cluster, 'centroid_vector') and getattr(cluster, 'centroid_vector', None) is not None:
            print_vector("Centroid vector của cluster", cluster.centroid_vector)
        else:
            print("\nCluster không có trường centroid_vector. Thông tin cluster:")
            for field in cluster._meta.fields:
                print(f"  {field.name}: {getattr(cluster, field.name)}")
    else:
        print("\nKhông xác định được cluster cho user này.")

    # 4. Sở thích nhóm (cluster preferences)
    if cluster and hasattr(cluster, "genre_preferences") and cluster.genre_preferences:
        print("\nCluster genre preferences (trung bình):")
        for genre_id, score in cluster.genre_preferences.items():
            print(f"  Genre {genre_id}: {score:.3f}")
    else:
        print("\nKhông có cluster genre preferences.")

    # 5. Sở thích cá nhân (user preferences)
    if user_pref and user_pref.genre_preferences:
        print("\nUser genre preferences:")
        for genre_id, score in user_pref.genre_preferences.items():
            print(f"  Genre {genre_id}: {score:.3f}")
    else:
        print("\nUser chưa có genre preferences.")

    # 6. Kết hợp sở thích cá nhân + nhóm (nếu có)
    if user_pref and user_pref.genre_preferences and cluster and cluster.genre_preferences:
        alpha = 0.7
        all_genres = set(user_pref.genre_preferences.keys()) | set(cluster.genre_preferences.keys())
        print("\nKết quả kết hợp sở thích cá nhân + nhóm (alpha=0.7):")
        for genre_id in all_genres:
            user_score = user_pref.genre_preferences.get(genre_id, 0)
            cluster_score = cluster.genre_preferences.get(genre_id, 0)
            final_score = alpha * user_score + (1 - alpha) * cluster_score
            print(f"  Genre {genre_id}: {final_score:.3f} (user: {user_score:.3f}, cluster: {cluster_score:.3f})")
    else:
        print("\nKhông đủ dữ liệu để kết hợp sở thích cá nhân + nhóm.")

if __name__ == "__main__":
    main()
