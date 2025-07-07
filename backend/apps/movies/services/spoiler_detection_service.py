import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SpoilerDetectionResult:
    """Result of spoiler detection analysis"""
    is_spoiler: bool
    confidence: float  # 0.0 to 1.0
    detected_patterns: List[str]
    spoiler_indicators: List[str]
    explanation: str
    suggested_action: str


class SpoilerDetectionService:
    """
    Service for detecting spoilers in movie reviews using multiple detection methods
    """

    def __init__(self):
        # Vietnamese spoiler keywords and patterns
        self.vi_spoiler_keywords = {
            'high_confidence': [
                # Kết thúc và kết cục
                'kết thúc', 'kết cục', 'kết thúc phim', 'kết thúc bộ phim', 'kết thúc câu chuyện',
                'đoạn cuối', 'phần cuối', 'cảnh cuối', 'scene cuối', 'ending', 'finale',
                'kết luận', 'kết quả cuối cùng', 'hậu quả', 'kết cục cuối cùng',

                # Cái chết và mất mạng
                'chết', 'bị giết', 'tự tử', 'hy sinh', 'mất mạng', 'qua đời', 'tử vong',
                'bị thương nặng', 'bị bắn', 'bị đâm', 'bị đánh chết', 'bị giết chết',
                'death', 'dies', 'killed', 'murdered', 'suicide', 'sacrifice',
                'bị bỏng', 'bị chết đuối', 'bị tai nạn', 'bị bệnh', 'bị ung thư',

                # Hôn nhân và tình cảm
                'cưới', 'kết hôn', 'ly hôn', 'chia tay', 'đính hôn', 'cầu hôn',
                'marriage', 'marries', 'divorce', 'breakup', 'proposal', 'wedding',
                'yêu nhau', 'yêu đương', 'tình yêu', 'tình cảm', 'romance',
                'bỏ nhau', 'ly dị', 'tái hôn', 'ngoại tình', 'phản bội tình cảm',

                # Phản bội và kẻ thù
                'phản bội', 'phản diện', 'kẻ thù', 'đối thủ', 'kẻ phản bội',
                'betrayal', 'villain', 'enemy', 'antagonist', 'traitor',
                'kẻ xấu', 'ác nhân', 'kẻ ác', 'kẻ thù', 'địch thủ',
                'phản diện', 'kẻ phản diện', 'kẻ thù chính', 'kẻ thù cuối cùng',

                # Bí mật và sự thật
                'bí mật', 'sự thật', 'thân phận', 'danh tính', 'bí ẩn',
                'secret', 'truth', 'identity', 'real identity', 'mystery',
                'sự thật ẩn giấu', 'bí mật gia đình', 'bí mật quá khứ',
                'danh tính thật', 'thân phận thật', 'sự thật đau lòng',

                # Twist và bất ngờ
                'twist', 'plot twist', 'bất ngờ', 'shock', 'surprise',
                'tình tiết bất ngờ', 'cốt truyện bất ngờ', 'diễn biến bất ngờ',
                'kết thúc bất ngờ', 'ending bất ngờ', 'twist ending',
                'bất ngờ cuối phim', 'shock ending', 'surprise ending',

                # Tiết lộ và khám phá
                'reveal', 'tiết lộ', 'khám phá ra', 'phát hiện ra', 'tìm ra',
                'discovered', 'found out', 'revealed', 'uncovered', 'exposed',
                'hóa ra', 'thực ra', 'sự thật là', 'turns out', 'actually',
                'truth is', 'in fact', 'as it turns out', 'surprisingly',

                # Cảnh báo spoiler
                'spoiler', 'spoiler alert', 'cảnh báo spoiler', 'spoiler warning',
                'chứa spoiler', 'có spoiler', 'spoiler ahead', 'spoiler content',
                'cảnh báo nội dung', 'cảnh báo tiết lộ', 'cảnh báo kết thúc',

                # Các tình tiết cụ thể
                'bị bắt', 'bị tù', 'bị xử tử', 'bị hành quyết', 'bị treo cổ',
                'bị chôn sống', 'bị chết đuối', 'bị cháy', 'bị nổ', 'bị sập',
                'bị lật xe', 'bị tai nạn máy bay', 'bị động đất', 'bị sóng thần',

                # Quan hệ gia đình
                'cha thật', 'mẹ thật', 'cha nuôi', 'mẹ nuôi', 'anh em ruột',
                'chị em ruột', 'con nuôi', 'cha mẹ nuôi', 'gia đình thật',
                'họ hàng thật', 'người thân thật', 'quan hệ huyết thống',

                # Tình tiết tình cảm
                'yêu nhầm người', 'yêu kẻ thù', 'yêu kẻ phản bội',
                'tình yêu cấm', 'tình yêu bí mật', 'tình yêu đau khổ',
                'chia tay vĩnh viễn', 'chia tay đau lòng', 'mất người yêu',

                # Tình tiết hành động
                'bị phục kích', 'bị phản bội', 'bị lừa gạt', 'bị lừa đảo',
                'bị mắc bẫy', 'bị bắt cóc', 'bị tống tiền', 'bị đe dọa',
                'bị theo dõi', 'bị rình rập', 'bị tấn công', 'bị đánh',

                # Tình tiết tâm lý
                'bị điên', 'bị mất trí', 'bị hoang tưởng', 'bị ảo giác',
                'bị trầm cảm', 'bị tự kỷ', 'bị tâm thần', 'bị rối loạn',
                'bị ám ảnh', 'bị sợ hãi', 'bị hoảng loạn', 'bị stress',

                # Tình tiết xã hội
                'bị sa thải', 'bị phá sản', 'bị mất việc', 'bị đuổi học',
                'bị bắt giam', 'bị kết án', 'bị tử hình', 'bị tù chung thân',
                'bị cấm', 'bị trục xuất', 'bị lưu đày', 'bị cách ly'
            ],
            'medium_confidence': [
                # Nhân vật chính
                'nhân vật chính', 'protagonist', 'hero', 'anh hùng', 'nữ chính',
                'main character', 'lead character', 'heroine', 'leading role',
                'nhân vật nam chính', 'nhân vật nữ chính', 'diễn viên chính',
                'vai chính', 'vai nam chính', 'vai nữ chính', 'vai diễn chính',

                # Nhân vật phản diện
                'villain', 'ác nhân', 'kẻ xấu', 'phản diện', 'kẻ thù',
                'antagonist', 'bad guy', 'evil character', 'villainous',
                'kẻ phản diện', 'kẻ ác', 'kẻ thù chính', 'kẻ thù phụ',
                'vai phản diện', 'vai ác', 'vai xấu', 'vai thù địch',

                # Cốt truyện và tình tiết
                'tình tiết', 'cốt truyện', 'diễn biến', 'plot', 'storyline',
                'narrative', 'story', 'tale', 'plot development', 'story arc',
                'cốt truyện chính', 'tình tiết chính', 'diễn biến chính',
                'câu chuyện', 'truyện', 'kịch bản', 'script', 'screenplay',

                # Quan hệ và tình cảm
                'quan hệ', 'tình cảm', 'tình yêu', 'relationship', 'romance',
                'love story', 'romantic', 'affair', 'dating', 'courtship',
                'tình bạn', 'tình đồng nghiệp', 'tình đồng chí', 'tình đồng đội',
                'quan hệ gia đình', 'quan hệ bạn bè', 'quan hệ công việc',

                # Gia đình
                'gia đình', 'cha mẹ', 'con cái', 'family', 'parents', 'children',
                'siblings', 'brothers', 'sisters', 'relatives', 'kin',
                'cha', 'mẹ', 'anh', 'chị', 'em', 'ông', 'bà', 'cô', 'chú',
                'father', 'mother', 'brother', 'sister', 'grandfather', 'grandmother',

                # Bạn bè và đồng nghiệp
                'bạn bè', 'đồng nghiệp', 'đối thủ', 'friends', 'colleagues', 'rivals',
                'partners', 'teammates', 'allies', 'enemies', 'competitors',
                'bạn thân', 'bạn cũ', 'bạn mới', 'đồng nghiệp cũ', 'đồng nghiệp mới',
                'đối thủ cũ', 'đối thủ mới', 'kẻ thù cũ', 'kẻ thù mới',

                # Nhiệm vụ và mục tiêu
                'nhiệm vụ', 'mục tiêu', 'mục đích', 'mission', 'goal', 'objective',
                'task', 'assignment', 'duty', 'responsibility', 'purpose',
                'nhiệm vụ quan trọng', 'mục tiêu cuối cùng', 'mục đích chính',
                'nhiệm vụ bí mật', 'mục tiêu bí mật', 'mục đích ẩn giấu',

                # Thử thách và khó khăn
                'thử thách', 'khó khăn', 'trở ngại', 'challenge', 'obstacle', 'difficulty',
                'problem', 'issue', 'trouble', 'hardship', 'adversity',
                'thử thách lớn', 'khó khăn lớn', 'trở ngại lớn', 'thử thách cuối cùng',
                'khó khăn cuối cùng', 'trở ngại cuối cùng', 'thử thách quan trọng',

                # Thành công và thất bại
                'thành công', 'thất bại', 'chiến thắng', 'success', 'failure', 'victory',
                'defeat', 'win', 'lose', 'achieve', 'accomplish', 'succeed',
                'thành công lớn', 'thất bại lớn', 'chiến thắng lớn', 'thành công cuối cùng',
                'thất bại cuối cùng', 'chiến thắng cuối cùng', 'thành công quan trọng',

                # Kết quả và hậu quả
                'kết quả', 'hậu quả', 'kết luận', 'result', 'consequence', 'outcome',
                'effect', 'impact', 'influence', 'conclusion', 'ending',
                'kết quả cuối cùng', 'hậu quả cuối cùng', 'kết luận cuối cùng',
                'kết quả quan trọng', 'hậu quả quan trọng', 'kết luận quan trọng',

                # Tình tiết hành động
                'hành động', 'action', 'fight', 'battle', 'war', 'conflict',
                'chiến đấu', 'đánh nhau', 'xung đột', 'đối đầu', 'đối kháng',
                'cảnh hành động', 'cảnh đánh nhau', 'cảnh chiến đấu', 'cảnh xung đột',
                'scene hành động', 'scene đánh nhau', 'scene chiến đấu', 'scene xung đột',

                # Tình tiết tình cảm
                'tình cảm', 'emotion', 'feeling', 'sentiment', 'passion', 'love',
                'cảm xúc', 'tình yêu', 'tình bạn', 'tình thương', 'tình cảm gia đình',
                'cảnh tình cảm', 'cảnh yêu đương', 'cảnh chia tay', 'cảnh hội ngộ',
                'scene tình cảm', 'scene yêu đương', 'scene chia tay', 'scene hội ngộ',

                # Tình tiết hài hước
                'hài hước', 'comedy', 'funny', 'humorous', 'joke', 'laugh',
                'vui nhộn', 'hài', 'buồn cười', 'đáng cười', 'hài hước',
                'cảnh hài hước', 'cảnh vui nhộn', 'cảnh buồn cười', 'cảnh đáng cười',
                'scene hài hước', 'scene vui nhộn', 'scene buồn cười', 'scene đáng cười',

                # Tình tiết kinh dị
                'kinh dị', 'horror', 'scary', 'frightening', 'terrifying', 'spooky',
                'đáng sợ', 'rùng rợn', 'ghê rợn', 'ma quái', 'quỷ quái',
                'cảnh kinh dị', 'cảnh đáng sợ', 'cảnh rùng rợn', 'cảnh ghê rợn',
                'scene kinh dị', 'scene đáng sợ', 'scene rùng rợn', 'scene ghê rợn',

                # Tình tiết bí ẩn
                'bí ẩn', 'mystery', 'mysterious', 'enigmatic', 'puzzling', 'confusing',
                'khó hiểu', 'khó giải thích', 'khó lý giải', 'khó hiểu',
                'cảnh bí ẩn', 'cảnh khó hiểu', 'cảnh khó giải thích', 'cảnh khó lý giải',
                'scene bí ẩn', 'scene khó hiểu', 'scene khó giải thích', 'scene khó lý giải'
            ],
            'low_confidence': [
                # Diễn xuất và biểu diễn
                'diễn xuất', 'acting', 'performance', 'role', 'character',
                'biểu diễn', 'vai diễn', 'nhân vật', 'personality', 'portrayal',
                'diễn viên', 'actor', 'actress', 'star', 'celebrity', 'performer',
                'vai nam', 'vai nữ', 'vai phụ', 'vai chính', 'vai diễn chính',
                'male role', 'female role', 'supporting role', 'leading role',

                # Đạo diễn và sản xuất
                'đạo diễn', 'director', 'filmmaker', 'producer', 'creator',
                'đạo diễn chính', 'đạo diễn phụ', 'đạo diễn trợ lý', 'đạo diễn thực tập',
                'main director', 'assistant director', 'co-director', 'executive producer',
                'nhà sản xuất', 'producer', 'executive producer', 'line producer',
                'production', 'filmmaking', 'cinema', 'movie making',

                # Kịch bản và viết lách
                'kịch bản', 'script', 'screenplay', 'writing', 'writer',
                'scenario', 'story', 'plot', 'narrative', 'dialogue',
                'tác giả', 'writer', 'author', 'screenwriter', 'scriptwriter',
                'nhà văn', 'novelist', 'playwright', 'dramatist', 'storyteller',
                'writing style', 'narrative style', 'storytelling', 'plot development',

                # Âm nhạc và âm thanh
                'âm nhạc', 'music', 'soundtrack', 'score', 'sound',
                'nhạc nền', 'background music', 'theme music', 'original score',
                'composer', 'musician', 'singer', 'song', 'melody', 'rhythm',
                'nhạc sĩ', 'ca sĩ', 'bài hát', 'giai điệu', 'nhịp điệu',
                'sound design', 'sound effects', 'audio', 'soundtrack album',

                # Hiệu ứng và kỹ thuật
                'hiệu ứng', 'effects', 'visual effects', 'special effects', 'vfx',
                'cgi', 'computer graphics', 'animation', '3d', 'digital effects',
                'hiệu ứng đặc biệt', 'hiệu ứng hình ảnh', 'hiệu ứng âm thanh',
                'special effects', 'visual effects', 'sound effects', 'practical effects',
                'stunt', 'stunt work', 'action sequence', 'fight choreography',

                # Bối cảnh và thiết kế
                'bối cảnh', 'setting', 'background', 'atmosphere', 'environment',
                'location', 'place', 'venue', 'scene', 'stage', 'set design',
                'production design', 'art direction', 'costume design', 'makeup',
                'thiết kế sản xuất', 'thiết kế nghệ thuật', 'thiết kế trang phục',
                'production design', 'art direction', 'costume design', 'makeup design',

                # Thời gian và giai đoạn
                'thời gian', 'time', 'period', 'era', 'epoch', 'age',
                'thời đại', 'giai đoạn', 'kỷ nguyên', 'thế kỷ', 'năm',
                'century', 'decade', 'year', 'month', 'day', 'hour',
                'quá khứ', 'hiện tại', 'tương lai', 'past', 'present', 'future',
                'historical', 'contemporary', 'modern', 'ancient', 'medieval',

                # Địa điểm và không gian
                'địa điểm', 'location', 'place', 'venue', 'site', 'spot',
                'thành phố', 'quốc gia', 'lục địa', 'hành tinh', 'vũ trụ',
                'city', 'country', 'continent', 'planet', 'universe', 'world',
                'vùng miền', 'khu vực', 'khu phố', 'con đường', 'tòa nhà',
                'region', 'area', 'district', 'street', 'building', 'house',

                # Kỹ thuật quay phim
                'quay phim', 'cinematography', 'camera', 'shot', 'angle',
                'camera work', 'filming', 'shooting', 'recording', 'capture',
                'cinematographer', 'director of photography', 'camera operator',
                'nhà quay phim', 'đạo diễn hình ảnh', 'người quay phim',
                'camera angle', 'shot composition', 'lighting', 'color grading',

                # Chỉnh sửa và hậu kỳ
                'chỉnh sửa', 'editing', 'cut', 'edit', 'post-production',
                'editor', 'film editor', 'video editor', 'cutting', 'splicing',
                'nhà dựng phim', 'người chỉnh sửa', 'biên tập viên',
                'film editing', 'video editing', 'sound editing', 'color correction',

                # Phân tích và đánh giá
                'phân tích', 'analysis', 'review', 'criticism', 'evaluation',
                'đánh giá', 'nhận xét', 'bình luận', 'comment', 'opinion',
                'critic', 'reviewer', 'analyst', 'evaluator', 'commentator',
                'nhà phê bình', 'người đánh giá', 'người nhận xét', 'người bình luận',
                'critical analysis', 'film criticism', 'movie review', 'cinema analysis',

                # Cảm xúc và phản ứng
                'cảm xúc', 'emotion', 'feeling', 'sentiment', 'mood', 'tone',
                'cảm giác', 'tâm trạng', 'tâm lý', 'tinh thần', 'tâm hồn',
                'emotional', 'sentimental', 'moody', 'atmospheric', 'touching',
                'cảm động', 'xúc động', 'tình cảm', 'tâm lý', 'tinh thần',

                # Phong cách và thể loại
                'phong cách', 'style', 'genre', 'type', 'category', 'form',
                'thể loại', 'loại phim', 'dạng phim', 'kiểu phim', 'mẫu phim',
                'drama', 'comedy', 'action', 'thriller', 'horror', 'romance',
                'kịch', 'hài', 'hành động', 'kinh dị', 'tình cảm', 'phiêu lưu',
                'artistic style', 'visual style', 'narrative style', 'directorial style'
            ]
        }

        # English spoiler keywords and patterns
        self.en_spoiler_keywords = {
            'high_confidence': [
                'ending', 'finale', 'conclusion', 'ending of the movie',
                'dies', 'killed', 'death', 'suicide', 'sacrifice',
                'marries', 'marriage', 'divorce', 'breakup',
                'betrayal', 'villain', 'enemy', 'antagonist',
                'secret', 'truth', 'identity', 'real identity',
                'twist', 'plot twist', 'surprise', 'shock',
                'end of movie', 'final scene', 'last part',
                'reveal', 'revealed', 'discovered',
                'turns out', 'actually', 'truth is',
                'spoiler', 'spoiler alert', 'warning'
            ],
            'medium_confidence': [
                'main character', 'protagonist', 'hero', 'heroine',
                'villain', 'antagonist', 'bad guy', 'enemy',
                'plot', 'storyline', 'narrative',
                'relationship', 'romance', 'love story',
                'family', 'parents', 'children',
                'friends', 'colleagues', 'rivals',
                'mission', 'goal', 'objective',
                'challenge', 'obstacle', 'difficulty',
                'success', 'failure', 'victory',
                'result', 'consequence', 'outcome'
            ],
            'low_confidence': [
                'acting', 'performance', 'role',
                'director', 'direction', 'filmmaking',
                'script', 'screenplay', 'writing',
                'music', 'soundtrack', 'score',
                'effects', 'visual effects', 'cinematography',
                'setting', 'background', 'atmosphere',
                'time period', 'era', 'historical',
                'location', 'place', 'setting'
            ]
        }

        # Spoiler patterns and indicators
        self.spoiler_patterns = {
            'future_tense_indicators': [
                r'\b(sẽ|will|going to|gonna)\b',
                r'\b(sau khi|after|when)\b',
                r'\b(cuối cùng|finally|eventually)\b'
            ],
            'reveal_indicators': [
                r'\b(hóa ra|turns out|actually|in fact)\b',
                r'\b(sự thật là|truth is|reveals that)\b',
                r'\b(khám phá ra|discovers|finds out)\b'
            ],
            'specific_plot_points': [
                r'\b(scene|scene where|moment when)\b',
                r'\b(part where|when|during)\b',
                r'\b(sequence|sequence where)\b'
            ],
            'character_development': [
                r'\b(character development|phát triển nhân vật)\b',
                r'\b(character arc|arc của nhân vật)\b',
                r'\b(transformation|biến đổi)\b'
            ]
        }

        # Context indicators that might reduce spoiler probability
        self.non_spoiler_indicators = [
            'review', 'đánh giá', 'opinion', 'nhận xét',
            'cinematography', 'quay phim', 'visual', 'hình ảnh',
            'acting', 'diễn xuất', 'performance', 'biểu diễn',
            'direction', 'đạo diễn', 'director', 'đạo diễn',
            'music', 'âm nhạc', 'soundtrack', 'nhạc nền',
            'pacing', 'nhịp độ', 'rhythm', 'tiết tấu',
            'atmosphere', 'không khí', 'mood', 'tâm trạng',
            'style', 'phong cách', 'tone', 'giọng điệu'
        ]

    def detect_spoilers(self, content: str, language: str = 'en', movie_title: str = None, thresholds: Dict = None) -> SpoilerDetectionResult:
        """
        Main method to detect spoilers in review content

        Args:
            content: Review content text
            language: Language code ('en' or 'vi')
            movie_title: Movie title for context analysis

        Returns:
            SpoilerDetectionResult with detection analysis
        """
        if not content or len(content.strip()) < 10:
            return SpoilerDetectionResult(
                is_spoiler=False,
                confidence=0.0,
                detected_patterns=[],
                spoiler_indicators=[],
                explanation="Content too short for spoiler analysis",
                suggested_action="manual_review"
            )

        # Normalize content
        normalized_content = self._normalize_content(content, language)

        # Run detection methods
        keyword_score = self._keyword_analysis(normalized_content, language)
        pattern_score = self._pattern_analysis(normalized_content, language)
        context_score = self._context_analysis(normalized_content, language, movie_title)
        length_score = self._length_analysis(content)

        # Combine scores with weights
        final_score = self._combine_scores({
            'keyword': keyword_score,
            'pattern': pattern_score,
            'context': context_score,
            'length': length_score
        })

        # Determine result
        confidence = final_score['total']

        # Use dynamic thresholds to determine is_spoiler
        if thresholds is None:
            thresholds = {'auto_mark': 0.8, 'flag_review': 0.6, 'suggest_warning': 0.4}

        # is_spoiler should be true if confidence meets the suggest_warning threshold
        is_spoiler = confidence >= thresholds['suggest_warning']

        # Generate explanation
        explanation = self._generate_explanation(final_score, language)
        suggested_action = self._suggest_action(confidence, final_score, thresholds)

        return SpoilerDetectionResult(
            is_spoiler=is_spoiler,
            confidence=confidence,
            detected_patterns=final_score.get('patterns', []),
            spoiler_indicators=final_score.get('indicators', []),
            explanation=explanation,
            suggested_action=suggested_action
        )

    def _normalize_content(self, content: str, language: str) -> str:
        """Normalize content for analysis"""
        # Convert to lowercase
        normalized = content.lower()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove punctuation for keyword matching
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        return normalized.strip()

    def _keyword_analysis(self, content: str, language: str) -> Dict:
        """Analyze content for spoiler keywords"""
        keywords = self.vi_spoiler_keywords if language == 'vi' else self.en_spoiler_keywords

        detected_keywords = []
        total_score = 0.0

        for confidence_level, keyword_list in keywords.items():
            weight = {'high_confidence': 0.8, 'medium_confidence': 0.5, 'low_confidence': 0.2}[confidence_level]

            for keyword in keyword_list:
                if keyword in content:
                    detected_keywords.append({
                        'keyword': keyword,
                        'confidence': confidence_level,
                        'weight': weight
                    })
                    total_score += weight

        # Normalize score (max possible score is around 2.0)
        normalized_score = min(total_score / 2.0, 1.0)

        return {
            'score': normalized_score,
            'detected_keywords': detected_keywords,
            'total_keywords': len(detected_keywords)
        }

    def _pattern_analysis(self, content: str, language: str) -> Dict:
        """Analyze content for spoiler patterns"""
        detected_patterns = []
        total_score = 0.0

        for pattern_type, patterns in self.spoiler_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    weight = {
                        'future_tense_indicators': 0.3,
                        'reveal_indicators': 0.7,
                        'specific_plot_points': 0.6,
                        'character_development': 0.4
                    }.get(pattern_type, 0.5)

                    detected_patterns.append({
                        'pattern': pattern,
                        'type': pattern_type,
                        'matches': len(matches),
                        'weight': weight
                    })
                    total_score += weight * len(matches)

        # Normalize score
        normalized_score = min(total_score / 3.0, 1.0)

        return {
            'score': normalized_score,
            'detected_patterns': detected_patterns,
            'total_patterns': len(detected_patterns)
        }

    def _context_analysis(self, content: str, language: str, movie_title: str = None) -> Dict:
        """Analyze context to determine if content is likely a spoiler"""
        # Check for non-spoiler indicators
        non_spoiler_count = 0
        for indicator in self.non_spoiler_indicators:
            if indicator in content:
                non_spoiler_count += 1

        # Higher non-spoiler indicators reduce spoiler probability
        context_score = max(0.0, 1.0 - (non_spoiler_count * 0.1))

        # Check for review-specific language
        review_indicators = ['review', 'đánh giá', 'opinion', 'nhận xét', 'thoughts', 'suy nghĩ']
        has_review_language = any(indicator in content for indicator in review_indicators)

        if has_review_language:
            context_score *= 0.7  # Reduce spoiler probability

        return {
            'score': context_score,
            'non_spoiler_indicators': non_spoiler_count,
            'has_review_language': has_review_language
        }

    def _length_analysis(self, content: str) -> Dict:
        """Analyze content length for spoiler probability"""
        # Longer reviews are more likely to contain spoilers
        length = len(content)

        if length < 50:
            return {'score': 0.1, 'reason': 'very_short'}
        elif length < 200:
            return {'score': 0.3, 'reason': 'short'}
        elif length < 500:
            return {'score': 0.5, 'reason': 'medium'}
        elif length < 1000:
            return {'score': 0.7, 'reason': 'long'}
        else:
            return {'score': 0.8, 'reason': 'very_long'}

    def _combine_scores(self, scores: Dict) -> Dict:
        """Combine different analysis scores with weights"""
        weights = {
            'keyword': 0.4,
            'pattern': 0.3,
            'context': 0.2,
            'length': 0.1
        }

        total_score = sum(scores[key]['score'] * weights[key] for key in weights.keys())

        # Collect all detected patterns and indicators
        patterns = []
        indicators = []

        if 'keyword' in scores:
            for kw in scores['keyword'].get('detected_keywords', []):
                indicators.append(f"Keyword: {kw['keyword']} ({kw['confidence']})")

        if 'pattern' in scores:
            for pattern in scores['pattern'].get('detected_patterns', []):
                patterns.append(f"{pattern['type']}: {pattern['pattern']}")

        return {
            'total': total_score,
            'components': scores,
            'patterns': patterns,
            'indicators': indicators
        }

    def _generate_explanation(self, final_score: Dict, language: str) -> str:
        """Generate human-readable explanation of the detection result"""
        total = final_score['total']

        if language == 'vi':
            if total > 0.8:
                return "Nội dung có khả năng cao chứa spoiler dựa trên từ khóa và mẫu câu được phát hiện."
            elif total > 0.6:
                return "Nội dung có khả năng chứa spoiler. Cần kiểm tra thủ công."
            elif total > 0.4:
                return "Nội dung có một số dấu hiệu spoiler nhưng không rõ ràng."
            else:
                return "Nội dung không có dấu hiệu spoiler rõ ràng."
        else:
            if total > 0.8:
                return "Content has high probability of containing spoilers based on detected keywords and patterns."
            elif total > 0.6:
                return "Content likely contains spoilers. Manual review recommended."
            elif total > 0.4:
                return "Content has some spoiler indicators but not conclusive."
            else:
                return "Content shows no clear spoiler indicators."

    def _suggest_action(self, confidence: float, final_score: Dict, thresholds: Dict = None) -> str:
        """Suggest action based on detection confidence"""
        if thresholds is None:
            # Fallback to default thresholds
            thresholds = {'auto_mark': 0.8, 'flag_review': 0.6, 'suggest_warning': 0.4}

        if confidence >= thresholds['auto_mark']:
            return "auto_mark_spoiler"
        elif confidence >= thresholds['flag_review']:
            return "flag_for_review"
        elif confidence >= thresholds['suggest_warning']:
            return "suggest_spoiler_warning"
        else:
            return "no_action"

    def get_spoiler_statistics(self, reviews: List) -> Dict:
        """Generate statistics about spoiler detection across multiple reviews"""
        total_reviews = len(reviews)
        spoiler_count = sum(1 for review in reviews if review.get('is_spoiler', False))

        # Analyze detection patterns
        detection_patterns = {}
        for review in reviews:
            if 'detection_result' in review:
                result = review['detection_result']
                for pattern in result.get('detected_patterns', []):
                    pattern_type = pattern.split(':')[0] if ':' in pattern else 'unknown'
                    detection_patterns[pattern_type] = detection_patterns.get(pattern_type, 0) + 1

        return {
            'total_reviews': total_reviews,
            'spoiler_count': spoiler_count,
            'spoiler_percentage': (spoiler_count / total_reviews * 100) if total_reviews > 0 else 0,
            'detection_patterns': detection_patterns,
            'average_confidence': sum(r.get('detection_result', {}).get('confidence', 0) for r in reviews) / total_reviews if total_reviews > 0 else 0
        }


# Global instance for easy access
spoiler_detector = SpoilerDetectionService()
