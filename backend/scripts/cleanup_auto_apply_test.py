from typing import Dict

from apps.movies.models import Movie, MovieReview, ModerationFeedback
from apps.users.models import User


def main() -> None:
    # Identify movies created by the auto-apply test
    movies_qs = Movie.objects.filter(title__startswith="AutoApply Test")

    # Related reviews and feedback
    reviews_qs = MovieReview.objects.filter(movie__in=movies_qs)
    feedback_qs = ModerationFeedback.objects.filter(review__in=reviews_qs)

    # Collect counts before deletion
    summary: Dict = {
        "movies_to_delete": movies_qs.count(),
        "reviews_to_delete": reviews_qs.count(),
        "feedback_to_delete": feedback_qs.count(),
    }

    # Delete in FK-safe order
    feedback_deleted = feedback_qs.delete()
    reviews_deleted = reviews_qs.delete()
    movies_deleted = movies_qs.delete()

    # Remove the test moderator user
    user_deleted = User.objects.filter(username="mod_auto").delete()

    summary.update(
        {
            "feedback_deleted": feedback_deleted[0],
            "reviews_deleted": reviews_deleted[0],
            "movies_deleted": movies_deleted[0],
            "users_deleted": user_deleted[0],
        }
    )

    # Print the result summary
    print(summary)


if __name__ == "__main__":
    main()


