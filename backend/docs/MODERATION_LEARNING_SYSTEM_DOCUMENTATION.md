# Hệ Thống Quản Lý Kiểm Duyệt Thông Minh (Moderation Learning System)

## Tổng Quan

Hệ thống Quản lý Kiểm duyệt Thông minh là một giải pháp tự động hóa việc phát hiện và kiểm duyệt spoiler trong các bình luận phim. Hệ thống sử dụng AI và machine learning để tự động phát hiện spoiler, đồng thời có khả năng học hỏi từ phản hồi của moderator để cải thiện độ chính xác theo thời gian.

## Kiến Trúc Hệ Thống

### 1. Các Thành Phần Chính

#### Backend Services

- **`ModerationLearningService`**: Dịch vụ học máy chính
- **`SpoilerDetectionService`**: Dịch vụ phát hiện spoiler
- **`ModerationConfig`**: Cấu hình threshold và tham số
- **`ModerationFeedback`**: Lưu trữ phản hồi từ moderator

#### Frontend Dashboard

- **Analytics**: Bảng điều khiển phân tích hiệu suất
- **Auto-marked Reviews**: Quản lý reviews được đánh dấu tự động
- **Admin Settings**: Cài đặt threshold và cấu hình
- **Learning Dashboard**: Theo dõi hoạt động học máy

## Chi Tiết Các Tính Năng

### 1. Hệ Thống Phát Hiện Spoiler Tự Động

#### Cách Hoạt Động

```python
# Quy trình phát hiện spoiler
1. User gửi review/comment
2. AI phân tích nội dung → confidence score (0-1)
3. So sánh với threshold:
   - ≥ 0.8: Auto-mark (tự động đánh dấu)
   - 0.6-0.8: Flag for review (gắn cờ để xem xét)
   - 0.4-0.6: Suggest warning (đề xuất cảnh báo)
   - < 0.4: Allow (cho phép)
```

#### Các Loại Phát Hiện Phổ Biến

Hệ thống có thể phát hiện 25+ loại spoiler khác nhau:

**Spoiler Cốt Truyện:**

- Spoil cốt truyện
- Spoil kết thúc
- Spoil tình tiết bất ngờ
- Spoil kết quả

**Spoiler Nhân Vật:**

- Tiết lộ cái chết nhân vật
- Spoil diễn biến nhân vật
- Tiết lộ danh tính
- Spoil thức tỉnh sức mạnh

**Spoiler Mối Quan Hệ:**

- Spoil chuyện tình cảm
- Spoil lời tỏ tình
- Spoil mối quan hệ

**Spoiler Hành Động:**

- Spoil hành vi phản bội
- Tiết lộ cảnh hy sinh
- Tiết lộ cảnh giải cứu
- Spoil trận chiến cuối

### 2. Dashboard Analytics (Bảng Phân Tích)

#### Metrics Chính

```json
{
  "summary": {
    "overall_accuracy": 0.85, // Độ chính xác tổng
    "total_feedback": 150, // Tổng feedback
    "learning_enabled": true, // Trạng thái học máy
    "accuracy_vs_target": 0.02 // So với mục tiêu
  },
  "volume_metrics": {
    "total_reviews": 5547, // Tổng reviews xử lý
    "auto_marked_reviews": 89, // Reviews tự động đánh dấu
    "pending_moderation": 234 // Chờ kiểm duyệt
  }
}
```

#### Time Range Filters

- **Tuần này** (7 ngày)
- **Tháng này** (30 ngày)
- **Quý này** (90 ngày)
- **Năm nay** (365 ngày)

#### Visualization Components

1. **Stats Cards**: Hiển thị metrics quan trọng
2. **Learning System Performance**: Precision, Recall, F1-Score
3. **Processing Trends**: Xu hướng xử lý theo thời gian
4. **Common Detection Types**: Loại phát hiện phổ biến
5. **Moderator Performance**: Hiệu suất từng moderator

### 3. Auto-marked Reviews Management

#### Tính Năng Chính

- **Danh sách reviews**: Hiển thị reviews được AI đánh dấu
- **Filters nâng cao**:
  - Trạng thái: Pending/Reviewed/All
  - Confidence range: 0.8-1.0
  - Date range: Từ ngày - đến ngày
- **Review details**:
  - Nội dung review
  - Confidence score
  - Detected patterns
  - User thông tin

#### Feedback Modal

Moderator có thể cung cấp feedback cho mỗi review:

```javascript
feedbackData = {
  feedbackType:
    "correct_spoiler" |
    "false_positive" |
    "missed_spoiler" |
    "correct_non_spoiler",
  moderatorDecision:
    "approve_as_spoiler" | "approve_as_non_spoiler" | "reject_review",
  isSpoilerCorrect: boolean,
  difficultyLevel: "easy" | "medium" | "hard",
  notes: string,
  timeSpentSeconds: number,
};
```

### 4. Learning System (Hệ Thống Học Máy)

#### Quy Trình Học

1. **Thu thập feedback**: Moderator đánh giá reviews
2. **Phân tích patterns**: Xác định patterns hiệu quả/không hiệu quả
3. **Điều chỉnh weights**: Cập nhật trọng số từ khóa
4. **Optimized thresholds**: Đề xuất threshold tối ưu
5. **Performance tracking**: Theo dõi cải thiện

#### Pattern Effectiveness Analysis

```python
pattern_effectiveness = {
  'plot_spoiler': {
    'total': 50,
    'correct': 45,
    'effectiveness': 0.9  // 90% hiệu quả
  }
}
```

#### Threshold Optimization

Hệ thống tự động đề xuất điều chỉnh threshold dựa trên:

- False positive rate
- False negative rate
- Overall accuracy
- Feedback patterns

### 5. Admin Settings (Cài Đặt Admin)

#### Threshold Configuration

```json
{
  "auto_mark_threshold": 0.8, // Ngưỡng tự động đánh dấu
  "flag_for_review_threshold": 0.6, // Ngưỡng gắn cờ
  "suggest_warning_threshold": 0.4, // Ngưỡng đề xuất cảnh báo
  "learning_enabled": true, // Bật/tắt học máy
  "accuracy_target": 0.85, // Mục tiêu độ chính xác
  "min_feedback_count": 20, // Tối thiểu feedback để học
  "learning_rate": 0.1 // Tốc độ học
}
```

#### Learning Controls

- **Toggle Learning**: Bật/tắt hệ thống học
- **Manual Adjustments**: Điều chỉnh threshold thủ công
- **Reset to Defaults**: Khôi phục cài đặt mặc định

## API Endpoints

### Analytics Endpoints

```http
GET /api/movies/reviews/moderation_analytics/?days=30
GET /api/movies/reviews/auto_marked_reviews/?page=1&page_size=20
GET /api/movies/feedback/accuracy_summary/?days=30
```

### Configuration Endpoints

```http
GET /api/movies/moderation-config/active_config/
POST /api/movies/moderation-config/update_thresholds/
POST /api/movies/moderation-config/toggle_learning/
```

### Feedback Endpoints

```http
POST /api/movies/reviews/{id}/submit_feedback/
GET /api/movies/feedback/?moderator={id}
```

## Database Schema

### Core Models

#### ModerationConfig

```python
class ModerationConfig(models.Model):
    auto_mark_threshold = models.FloatField(default=0.8)
    flag_for_review_threshold = models.FloatField(default=0.6)
    suggest_warning_threshold = models.FloatField(default=0.4)
    learning_enabled = models.BooleanField(default=True)
    accuracy_target = models.FloatField(default=0.85)
    min_feedback_count = models.IntegerField(default=20)
    learning_rate = models.FloatField(default=0.1)
    is_active = models.BooleanField(default=True)
```

#### ModerationFeedback

```python
class ModerationFeedback(models.Model):
    review = models.ForeignKey(MovieReview)
    moderator = models.ForeignKey(User)
    feedback_type = models.CharField(max_length=50)
    moderator_decision = models.CharField(max_length=50)
    is_spoiler_correct = models.BooleanField()
    difficulty_level = models.CharField(max_length=20)
    original_confidence = models.FloatField()
    time_spent_seconds = models.IntegerField()
    notes = models.TextField(blank=True)
    used_for_learning = models.BooleanField(default=False)
```

#### MovieReview (Extended)

```python
class MovieReview(models.Model):
    # ... existing fields ...
    spoiler_confidence = models.FloatField(null=True, blank=True)
    spoiler_detected_patterns = models.JSONField(null=True, blank=True)
    spoiler_suggested_action = models.CharField(max_length=50, blank=True)
    auto_marked = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(User, null=True, blank=True)
    moderation_notes = models.TextField(blank=True)
```

## Performance Optimization

### Caching Strategy

```python
# Cache accuracy metrics for 1 hour
cache_key = f"accuracy_metrics_{days}d"
cache.set(cache_key, metrics, timeout=3600)

# Cache detection weights for 24 hours
cache.set('spoiler_detection_weights', keyword_weights, timeout=86400)
```

### Database Optimization

- Index trên `created_at`, `spoiler_confidence`
- Prefetch related objects để giảm queries
- Pagination cho large datasets
- Connection pooling

### Query Optimization

```python
# Efficient filtering
reviews_with_patterns = MovieReview.objects.filter(
    review_type='USER',
    created_at__gte=start_date,
    spoiler_detected_patterns__isnull=False
).exclude(spoiler_detected_patterns=[])

# Select related for joins
feedback_queryset = ModerationFeedback.objects.filter(
    created_at__gte=start_date
).select_related('review', 'moderator')
```

## Security & Permissions

### Role-based Access

- **Admin**: Full access to all features
- **Moderator**: Access to moderation tools và analytics
- **User**: Only submit reviews/feedback

### Permission Classes

```python
@action(detail=False, permission_classes=[IsAuthenticated])
def moderation_analytics(self, request):
    # Check if user is moderator or admin
    if not request.user.is_staff and not request.user.groups.filter(
        name__in=['Moderators', 'Administrators']
    ).exists():
        return Response({'status': 'error', 'message': 'Permission denied'})
```

## Monitoring & Logging

### Key Metrics to Monitor

- **Accuracy Trends**: Theo dõi độ chính xác theo thời gian
- **False Positive Rate**: Tỷ lệ phát hiện sai
- **Processing Volume**: Số lượng reviews xử lý
- **Learning Effectiveness**: Hiệu quả của việc học máy

### Logging Strategy

```python
logger.info(f"Applied automatic threshold adjustments: {suggestions}")
logger.error(f"Error calculating detection categories: {str(e)}")
logger.debug(f"Pattern effectiveness analysis: {pattern_analysis}")
```

## Troubleshooting

### Common Issues

#### 1. Learning System Not Improving

**Nguyên nhân**: Không đủ feedback data
**Giải pháp**: Tăng `min_feedback_count` hoặc khuyến khích moderator feedback

#### 2. High False Positive Rate

**Nguyên nhân**: Threshold quá thấp
**Giải pháp**: Tăng `auto_mark_threshold` hoặc để hệ thống tự điều chỉnh

#### 3. Performance Issues

**Nguyên nhân**: Large dataset, queries không tối ưu
**Giải pháp**: Implement caching, optimize queries, add indexes

### Debug Commands

```bash
# Check learning service status
python manage.py shell -c "
from apps.movies.services.moderation_learning_service import learning_service
print(learning_service.get_learning_status())
"

# Analyze pattern effectiveness
python manage.py shell -c "
from apps.movies.services.moderation_learning_service import learning_service
print(learning_service._analyze_detection_patterns())
"
```

## Future Enhancements

### 1. Advanced ML Features

- Deep learning models for better detection
- Multi-language spoiler detection
- Context-aware analysis

### 2. Enhanced Analytics

- Predictive analytics
- A/B testing for thresholds
- Real-time dashboards

### 3. Integration Features

- External ML services integration
- Automated reporting
- Mobile moderator app

## Conclusion

Hệ thống Quản lý Kiểm duyệt Thông minh cung cấp một giải pháp toàn diện cho việc phát hiện và quản lý spoiler tự động. Với khả năng học hỏi và cải thiện theo thời gian, hệ thống giúp giảm tải công việc cho moderator trong khi duy trì chất lượng kiểm duyệt cao.

---

**Phiên bản**: 2.0
**Ngày cập nhật**: December 2024
**Tác giả**: Movie Mate Development Team
