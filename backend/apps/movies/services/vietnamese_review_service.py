import logging
import random
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db import models

from ..models import Movie, MovieReview
from apps.users.models import User

logger = logging.getLogger(__name__)

class VietnameseReviewService:
    """Service for creating and managing Vietnamese movie reviews"""

    # Vietnamese review templates by rating range
    REVIEW_TEMPLATES = {
        'excellent': {  # 4.5-5.0 stars
            'titles': [
                'Phim tuyệt vời!',
                'Kiệt tác điện ảnh',
                'Không thể bỏ lỡ!',
                'Phim hay nhất năm',
                'Xuất sắc từ đầu đến cuối',
                'Đáng xem nhiều lần'
            ],
            'content_templates': [
                'Phim thực sự xuất sắc! {movie_title} đã mang đến cho tôi trải nghiệm điện ảnh tuyệt vời. Diễn xuất chuyên nghiệp, kịch bản hấp dẫn và hình ảnh đẹp mắt. Chắc chắn sẽ xem lại nhiều lần!',
                '{movie_title} là một kiệt tác thực thụ. Từ cảnh quay đầu tiên đến cuối phim, tôi hoàn toàn bị cuốn hút. Thông điệp sâu sắc và ý nghĩa. Đây là loại phim mà ai cũng nên xem ít nhất một lần.',
                'Tôi rất ấn tượng với {movie_title}. Phim có cốt truyện logic, nhân vật được phát triển tốt và diễn xuất tự nhiên. Đặc biệt là phần kết rất cảm động. Đánh giá cao!',
                'Phim hay đến mức khó tả! {movie_title} đã vượt xa mong đợi của tôi. Mọi chi tiết đều được chăm chút kỹ lưỡng. Đây chính là lý do tôi yêu điện ảnh!'
            ]
        },
        'good': {  # 3.5-4.4 stars
            'titles': [
                'Phim khá hay',
                'Đáng xem!',
                'Không tệ',
                'Khá thú vị',
                'Giải trí tốt',
                'Đáng thời gian'
            ],
            'content_templates': [
                '{movie_title} là một bộ phim khá hay với nhiều điểm sáng. Tuy có vài khuyết điểm nhỏ nhưng nhìn chung vẫn rất giải trí. Diễn viên diễn tốt và cốt truyện hấp dẫn.',
                'Tôi thích {movie_title}. Phim có nội dung thú vị và hình ảnh đẹp. Một số phân đoạn hơi chậm nhưng tổng thể vẫn đáng xem. Phù hợp để xem vào cuối tuần.',
                'Phim khá ổn! {movie_title} mang đến những giây phút giải trí nhẹ nhàng. Không quá xuất sắc nhưng cũng không tệ. Đánh giá tích cực.',
                '{movie_title} có lối kể chuyện hay và nhân vật đáng yêu. Tuy không phải kiệt tác nhưng đủ sức hút để xem từ đầu đến cuối.'
            ]
        },
        'average': {  # 2.5-3.4 stars
            'titles': [
                'Bình thường',
                'Có thể xem được',
                'Không đặc biệt',
                'Tạm ổn',
                'Trung bình',
                'Có điểm hay'
            ],
            'content_templates': [
                '{movie_title} là phim trung bình. Có vài điểm hay nhưng cũng có những phần khá nhàm chán. Nếu không có gì khác để xem thì có thể coi.',
                'Phim không tệ nhưng cũng không đặc biệt. {movie_title} có nội dung khá dễ đoán và diễn xuất bình thường. Chỉ xem một lần là đủ.',
                'Cảm giác lẫn lộn về {movie_title}. Một số phân cảnh hay nhưng tổng thể thiếu điểm nhấn. Có thể xem để giải trí nhẹ.',
                '{movie_title} có tiềm năng nhưng chưa khai thác hết. Cốt truyện ổn nhưng cách triển khai chưa thực sự thuyết phục.'
            ]
        },
        'poor': {  # 1.5-2.4 stars
            'titles': [
                'Hơi thất vọng',
                'Không hay lắm',
                'Chưa thỏa mãn',
                'Kỳ vọng cao hơn',
                'Có vấn đề',
                'Không ấn tượng'
            ],
            'content_templates': [
                'Thành thật mà nói, {movie_title} khiến tôi hơi thất vọng. Cốt truyện thiếu logic và diễn xuất chưa thực sự thuyết phục. Có thể là do kỳ vọng quá cao.',
                'Phim có vài điểm sáng nhưng nhìn chung {movie_title} chưa đạt được sự mong đợi. Cách kể chuyện hơi rối và nhân vật phát triển chưa tốt.',
                '{movie_title} không tệ hoàn toàn nhưng có nhiều điểm cần cải thiện. Đặc biệt là phần kịch bản và nhịp phim hơi chậm.',
                'Cảm giác {movie_title} còn thiếu gì đó để trở nên thực sự hấp dẫn. Tôi đã cố gắng theo dõi nhưng khó tập trung.'
            ]
        },
        'bad': {  # 1.0-1.4 stars
            'titles': [
                'Không khuyên xem',
                'Thất vọng',
                'Lãng phí thời gian',
                'Không hay',
                'Tệ quá',
                'Khó xem'
            ],
            'content_templates': [
                'Thành thật mà nói, {movie_title} thực sự khiến tôi thất vọng. Cốt truyện rời rạc, diễn xuất gượng ép và nhiều chi tiết không hợp lý. Không khuyên các bạn xem.',
                'Tôi đã cố gắng xem hết {movie_title} nhưng thực sự rất khó khăn. Phim thiếu điểm nhấn và khá nhàm chán. Có lẽ không phù hợp với tôi.',
                '{movie_title} không đạt được kỳ vọng của tôi. Nhiều phân cảnh kéo dài không cần thiết và cách kể chuyện chưa hấp dẫn.',
                'Rất tiếc phải nói rằng {movie_title} không phải là loại phim tôi thích. Có thể sẽ phù hợp với người khác nhưng với tôi thì không.'
            ]
        }
    }

    @classmethod
    def _get_rating_category(cls, rating: float) -> str:
        """Determine rating category based on score"""
        if rating >= 4.5:
            return 'excellent'
        elif rating >= 3.5:
            return 'good'
        elif rating >= 2.5:
            return 'average'
        elif rating >= 1.5:
            return 'poor'
        else:
            return 'bad'

    @classmethod
    def generate_vietnamese_review(cls, movie: Movie, rating: float, user: User = None) -> Dict[str, str]:
        """Generate a Vietnamese review for a movie"""
        category = cls._get_rating_category(rating)
        templates = cls.REVIEW_TEMPLATES[category]

        # Select random title and content
        title = random.choice(templates['titles'])
        content_template = random.choice(templates['content_templates'])

        # Format content with movie title
        movie_title = movie.get_title('vi') or movie.title or 'phim này'
        content = content_template.format(movie_title=movie_title)

        return {
            'title': title,
            'content': content,
            'rating': rating,
            'language': 'vi'
        }

    @classmethod
    def create_vietnamese_review(cls, movie: Movie, user: User, rating: float,
                               custom_title: str = None, custom_content: str = None) -> Optional[MovieReview]:
        """Create a Vietnamese review for a movie"""
        try:
            with transaction.atomic():
                # Check if review already exists
                existing_review = MovieReview.objects.filter(
                    movie=movie,
                    user=user,
                    review_type='USER'
                ).first()

                if existing_review:
                    logger.warning(f"Review already exists for user {user.username} and movie {movie.imdb_id}")
                    return existing_review

                # Generate review content if not provided
                if not custom_title or not custom_content:
                    generated = cls.generate_vietnamese_review(movie, rating, user)
                    title = custom_title or generated['title']
                    content = custom_content or generated['content']
                else:
                    title = custom_title
                    content = custom_content

                # Create review
                review = MovieReview.objects.create(
                    movie=movie,
                    user=user,
                    title=title,
                    content=content,
                    rating=Decimal(str(rating)),
                    review_type='USER',
                    language='vi',
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )

                logger.info(f"Created Vietnamese review for movie {movie.imdb_id} by user {user.username}")
                return review

        except Exception as e:
            logger.error(f"Error creating Vietnamese review: {str(e)}")
            return None

    @classmethod
    def create_batch_vietnamese_reviews(cls, movie_user_ratings: List[Tuple[Movie, User, float]],
                                      batch_size: int = 100) -> Dict[str, int]:
        """Create multiple Vietnamese reviews in batches"""
        created = 0
        skipped = 0
        errors = 0

        for i in range(0, len(movie_user_ratings), batch_size):
            batch = movie_user_ratings[i:i + batch_size]

            for movie, user, rating in batch:
                try:
                    review = cls.create_vietnamese_review(movie, user, rating)
                    if review:
                        created += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.error(f"Error in batch creation: {str(e)}")
                    errors += 1

        return {
            'created': created,
            'skipped': skipped,
            'errors': errors,
            'total': len(movie_user_ratings)
        }

    @classmethod
    def translate_existing_review(cls, review: MovieReview) -> Optional[str]:
        """Translate an existing review to Vietnamese (placeholder for translation service)"""
        # This is a placeholder - in production you would use a translation API
        # like Google Translate, Azure Translator, or a custom ML model

        if review.language == 'vi':
            return review.content

        # For now, generate a new Vietnamese review based on rating
        if review.movie and review.rating:
            generated = cls.generate_vietnamese_review(
                review.movie,
                float(review.rating)
            )
            return generated['content']

        return None

    @classmethod
    def get_vietnamese_reviews(cls, movie: Movie, limit: int = 10) -> List[MovieReview]:
        """Get Vietnamese reviews for a movie"""
        return MovieReview.objects.filter(
            movie=movie,
            review_type='USER',
            language='vi'
        ).order_by('-created_at')[:limit]

    @classmethod
    def get_review_statistics(cls, language: str = 'vi') -> Dict[str, int]:
        """Get review statistics for Vietnamese reviews"""
        if language == 'vi':
            reviews = MovieReview.objects.filter(language='vi', review_type='USER')
        else:
            reviews = MovieReview.objects.filter(review_type='USER')

        total = reviews.count()
        if total == 0:
            return {'total': 0}

        # Rating distribution
        rating_counts = {}
        for i in range(1, 6):
            count = reviews.filter(rating__gte=i, rating__lt=i+1).count()
            rating_counts[f'{i}_star'] = count

        return {
            'total': total,
            'rating_distribution': rating_counts,
            'average_rating': reviews.aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or 0
        }
