from django.db.models import Count
from apps.users.models import User
from apps.movies.models import Movie, MovieReview

print("=== CF DATABASE TEST ===")

# Basic stats
total_users = User.objects.count()
total_movies = Movie.objects.count()
total_ratings = MovieReview.objects.filter(
    review_type='USER',
    rating__isnull=False
).count()

print(f"Total Users: {total_users}")
print(f"Total Movies: {total_movies}")
print(f"Total Ratings: {total_ratings}")

# Users and movies with ratings
users_with_ratings = User.objects.filter(
    moviereview__review_type='USER',
    moviereview__rating__isnull=False
).distinct().count()

movies_with_ratings = Movie.objects.filter(
    moviereview__review_type='USER',
    moviereview__rating__isnull=False
).distinct().count()

print(f"Users with ratings: {users_with_ratings}")
print(f"Movies with ratings: {movies_with_ratings}")

# Sparsity
if users_with_ratings > 0 and movies_with_ratings > 0:
    possible_ratings = users_with_ratings * movies_with_ratings
    sparsity = 1 - (total_ratings / possible_ratings)
    print(f"Sparsity: {sparsity:.2%}")

# Rating distribution
rating_dist = MovieReview.objects.filter(
    review_type='USER',
    rating__isnull=False
).values('rating').annotate(
    count=Count('id')
).order_by('rating')

print("\nRating Distribution:")
for item in rating_dist:
    print(f"  {item['rating']} stars: {item['count']}")

# Cold start
cold_start_users = User.objects.filter(
    moviereview__review_type='USER',
    moviereview__rating__isnull=False
).annotate(
    rating_count=Count('moviereview')
).filter(rating_count__lt=5).count()

print(f"\nCold start users (<5 ratings): {cold_start_users}")
