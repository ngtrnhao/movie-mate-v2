from django.utils import timezone
import random

from apps.movies.models import (
    ModerationConfig,
    Movie,
    MovieReview,
    ModerationFeedback,
)
from apps.users.models import User
from apps.movies.services.moderation_learning_service import learning_service


def main() -> None:
    # 1) Set minimal valid thresholds while preserving order
    config = ModerationConfig.get_active_config()
    config.auto_mark_threshold = 0.06
    config.flag_for_review_threshold = 0.05
    config.suggest_warning_threshold = 0.04
    config.learning_enabled = True
    config.min_feedback_count = 10
    config.save()

    # 2) Ensure a moderator user exists for feedback ownership
    moderator_user, _ = User.objects.get_or_create(
        username="mod_auto",
        defaults={
            "email": "mod_auto@example.com",
            "is_staff": True,
        },
    )

    # 3) Create a movie to attach reviews
    movie = Movie.objects.create(title=f"AutoApply Test {timezone.now().timestamp()}")

    # 4) Create 60 reviews + feedback near thresholds (±0.08 around each base)
    created_feedback = []
    for base_threshold in [0.06, 0.05, 0.04]:
        for _ in range(20):
            confidence_value = max(0.0, min(1.0, base_threshold + random.uniform(-0.08, 0.08)))

            # Use EXTERNAL review type to satisfy constraints and avoid unique (user, movie)
            review = MovieReview.objects.create(
                movie=movie,
                review_type="EXTERNAL",
                external_username=f"ext_user_{random.randint(1, 10_000_000)}",
                external_review_id=str(random.randint(1, 10_000_000)),
                content="auto test review",
                is_public=True,
                language="en",
                spoiler_confidence=confidence_value,
                is_spoiler=False,
                spoiler_suggested_action="manual_review",
            )

            feedback = ModerationFeedback.objects.create(
                review=review,
                moderator=moderator_user,
                original_confidence=confidence_value,
                original_suggested_action="manual_review",
                original_is_spoiler=(confidence_value >= 0.04),
                feedback_type=random.choice(
                    [
                        "correct_spoiler",
                        "false_positive",
                        "missed_spoiler",
                        "correct_non_spoiler",
                    ]
                ),
                moderator_decision=random.choice(
                    [
                        "approve_as_spoiler",
                        "approve_as_non_spoiler",
                    ]
                ),
                is_spoiler_correct=random.choice([True, False]),
            )
            created_feedback.append(feedback)

    # 5) Trigger learning on the latest feedback, which should auto-apply if confidence > 0.8
    learning_result = learning_service.process_feedback(created_feedback[-1])

    # 6) Read updated thresholds
    updated = ModerationConfig.get_active_config()
    print(
        {
            "learning_result": learning_result,
            "updated_thresholds": {
                "auto_mark": updated.auto_mark_threshold,
                "flag_for_review": updated.flag_for_review_threshold,
                "suggest_warning": updated.suggest_warning_threshold,
            },
        }
    )


if __name__ == "__main__":
    main()


