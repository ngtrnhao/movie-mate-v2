#!/usr/bin/env python
"""
Tạo database indexes cho Collaborative Filtering
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import connection

def create_cf_indexes():
    """Tạo database indexes cho CF"""
    print("🔧 CREATING DATABASE INDEXES FOR COLLABORATIVE FILTERING")
    print("=" * 60)

    indexes = [
        # MovieReview indexes
        """
        CREATE INDEX IF NOT EXISTS idx_moviereview_user_type_rating
        ON movies_moviereview (user_id, review_type, rating)
        WHERE review_type = 'USER' AND rating IS NOT NULL;
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_moviereview_movie_user
        ON movies_moviereview (movie_id, user_id)
        WHERE review_type = 'USER';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_moviereview_rating_distribution
        ON movies_moviereview (rating)
        WHERE review_type = 'USER' AND rating IS NOT NULL;
        """,

        # UserSimilarity indexes
        """
        CREATE INDEX IF NOT EXISTS idx_usersimilarity_user1_user2
        ON recommendations_usersimilarity (user1_id, user2_id);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_usersimilarity_score_type
        ON recommendations_usersimilarity (similarity_score, similarity_type)
        WHERE similarity_type = 'collaborative';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_usersimilarity_user1_score
        ON recommendations_usersimilarity (user1_id, similarity_score)
        WHERE similarity_type = 'collaborative';
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_usersimilarity_user2_score
        ON recommendations_usersimilarity (user2_id, similarity_score)
        WHERE similarity_type = 'collaborative';
        """,

        # RecommendationResult indexes
        """
        CREATE INDEX IF NOT EXISTS idx_recommendationresult_user_type
        ON recommendations_recommendationresult (user_id, recommendation_type);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_recommendationresult_score
        ON recommendations_recommendationresult (score)
        WHERE recommendation_type = 'collaborative';
        """
    ]

    try:
        with connection.cursor() as cursor:
            for i, index_sql in enumerate(indexes, 1):
                try:
                    print(f"   📋 Creating index {i}/{len(indexes)}...")
                    cursor.execute(index_sql)
                    print(f"   ✅ Index {i} created successfully")
                except Exception as e:
                    print(f"   ⚠️ Index {i} error: {str(e)}")

            # Commit changes
            connection.commit()
            print(f"\n✅ All indexes created successfully!")

    except Exception as e:
        print(f"❌ Error creating indexes: {str(e)}")

    # Verify indexes
    print(f"\n🔍 VERIFYING INDEXES:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()

            print("   📋 Created indexes:")
            for index in indexes:
                print(f"      - {index[0]} on {index[1]}")

    except Exception as e:
        print(f"   ❌ Error verifying indexes: {str(e)}")

    print("=" * 60)

if __name__ == "__main__":
    create_cf_indexes()
