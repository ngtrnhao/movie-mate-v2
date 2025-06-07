import os
import django
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.tasks import sync_popular_movies, sync_top_rated_movies, sync_upcoming_movies

def main():
    """Test IMDB data synchronization"""
    print("Starting IMDB data synchronization test...")

    # Test popular movies sync
    print("\nSyncing popular movies...")
    result = sync_popular_movies()
    print(f"Result: {result}")

    # Test top rated movies sync
    print("\nSyncing top rated movies...")
    result = sync_top_rated_movies()
    print(f"Result: {result}")

    # Test upcoming movies sync
    print("\nSyncing upcoming movies...")
    result = sync_upcoming_movies()
    print(f"Result: {result}")

    print("\nTest completed!")

if __name__ == '__main__':
    main()
