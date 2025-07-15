# Spoiler Detection System - Implementation Plan

## 📋 Tóm tắt triển khai

Tài liệu này mô tả chi tiết kế hoạch triển khai hệ thống cải tiến spoiler detection với các tính năng:

1. **Auto-marked Tab**: Tab hiển thị reviews đã được auto-mark spoiler để moderator review lại
2. **False Positive/Negative Tracking**: Hệ thống tracking và learning từ feedback của moderator
3. **Dynamic Thresholds**: Admin có thể cấu hình thresholds mà không cần sửa code
4. **Enhanced Analytics**: Thống kê chi tiết về performance và accuracy

## 🎯 Mục tiêu

- **Giảm false positive/negative**: Học từ feedback để cải thiện accuracy
- **Tăng hiệu quả moderator**: Cho phép review lại auto-marked content
- **Flexibility**: Admin có thể điều chỉnh thresholds theo nhu cầu thực tế
- **Transparency**: Statistics chi tiết về performance của hệ thống

## 📊 Hiện trạng hệ thống

### Backend (Django)

**Spoiler Detection Service** (`/backend/apps/movies/services/spoiler_detection_service.py`):

- ✅ Đã có logic phân tích spoiler với confidence scoring
- ✅ Có 4 suggested actions: `auto_mark_spoiler`, `flag_for_review`, `suggest_spoiler_warning`, `no_action`
- ✅ Current thresholds:
  - `> 0.8`: auto_mark_spoiler
  - `0.6-0.8`: flag_for_review
  - `0.4-0.6`: suggest_spoiler_warning
  - `≤ 0.4`: no_action

**MovieReview Model** (`/backend/apps/movies/models.py`):

- ✅ Đã có các trường: `is_spoiler`, `spoiler_confidence`, `spoiler_suggested_action`, `auto_marked`
- ✅ Có moderation fields: `is_approved`, `moderated_by`, `moderated_at`, `moderation_reason`

### Frontend (React)

**Moderator Dashboard** (`/frontend/src/pages/Moderator/Dashboard.jsx`):

- ✅ Có cấu trúc dashboard với multiple tabs
- ✅ Có ContentModerationDashboard component
- ⚠️ Chưa có tab cho auto-marked reviews
- ⚠️ Chưa có interface để configure thresholds

## 🚀 Implementation Roadmap

### Phase 1: Backend Infrastructure (2-3 ngày)

#### 1.1 ModerationConfig Model

```python
class ModerationConfig(models.Model):
    # Dynamic thresholds
    auto_mark_threshold = models.FloatField(default=0.8)
    flag_for_review_threshold = models.FloatField(default=0.6)
    suggest_warning_threshold = models.FloatField(default=0.4)

    # Learning parameters
    learning_enabled = models.BooleanField(default=True)
    learning_rate = models.FloatField(default=0.1)
    min_feedback_count = models.IntegerField(default=10)

    # System settings
    auto_moderate_enabled = models.BooleanField(default=True)
    require_approval_for_auto_marked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 1.2 ModerationFeedback Model

```python
class ModerationFeedback(models.Model):
    FEEDBACK_TYPES = [
        ('correct_spoiler', 'Correctly Marked as Spoiler'),
        ('false_positive', 'False Positive - Not a Spoiler'),
        ('missed_spoiler', 'False Negative - Missed Spoiler'),
        ('correct_non_spoiler', 'Correctly Marked as Non-Spoiler'),
    ]

    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE)
    moderator = models.ForeignKey('users.User', on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=32, choices=FEEDBACK_TYPES)
    original_confidence = models.FloatField()
    original_suggested_action = models.CharField(max_length=32)
    moderator_decision = models.CharField(max_length=32)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

#### 1.3 Enhanced API Endpoints

```python
# Trong movies/views.py
@action(detail=False, methods=['get'])
def auto_marked_reviews(self, request):
    """Get reviews that were auto-marked as spoiler"""

@action(detail=False, methods=['get'])
def moderation_analytics(self, request):
    """Get detailed moderation analytics"""

@action(detail=True, methods=['post'])
def submit_feedback(self, request, pk=None):
    """Submit moderator feedback for learning"""
```

### Phase 2: Learning Algorithm (1-2 ngày)

#### 2.1 Feedback Processing Service

```python
class ModerationLearningService:
    def process_feedback(self, feedback):
        """Process moderator feedback to adjust system"""

    def calculate_accuracy_metrics(self):
        """Calculate precision, recall, F1-score"""

    def suggest_threshold_adjustments(self):
        """Suggest optimal thresholds based on feedback"""

    def update_detection_weights(self):
        """Adjust detection algorithm weights"""
```

#### 2.2 Auto-Adjustment Logic

- Track accuracy metrics theo từng confidence range
- Tự động suggest threshold adjustments
- Optional: Auto-apply adjustments nếu confidence đủ cao

### Phase 3: Frontend Auto-marked Tab (1-2 ngày)

#### 3.1 AutoMarkedReviewsTab Component

```jsx
const AutoMarkedReviewsTab = () => {
  // Tab riêng cho auto-marked reviews
  // Cho phép moderator review lại quyết định
  // Bulk actions để confirm/reverse multiple reviews
  // Filter theo confidence level, date range
};
```

#### 3.2 Enhanced ContentModerationDashboard

- Add tab cho "Auto-marked Reviews"
- Statistics panel cho accuracy metrics
- Feedback submission interface

### Phase 4: Admin Configuration Interface (1 ngày)

#### 4.1 AdminThresholdConfig Component

```jsx
const AdminThresholdConfig = () => {
  // Interface để configure thresholds
  // Real-time preview của impact
  // Safety checks để prevent extreme values
  // History tracking của threshold changes
};
```

#### 4.2 Analytics Dashboard

```jsx
const ModerationAnalytics = () => {
  // Accuracy metrics over time
  // False positive/negative trends
  // Performance by moderator
  // System health indicators
};
```

### Phase 5: Testing & Integration (1 ngày)

#### 5.1 Unit Tests

- Test models và validation logic
- Test API endpoints với different scenarios
- Test learning algorithm với mock data

#### 5.2 Integration Tests

- End-to-end workflow testing
- UI component testing
- Performance testing với large datasets

## 🛠️ Technical Implementation Details

### Database Migrations Required

1. **Add ModerationConfig table**
2. **Add ModerationFeedback table**
3. **Add indexes for performance**:
   - `auto_marked` field trong MovieReview
   - Composite indexes cho analytics queries

### API Response Format Updates

```json
{
  "auto_marked_reviews": {
    "results": [...],
    "count": 25,
    "accuracy_rate": 0.87,
    "pending_review_count": 15
  },
  "analytics": {
    "accuracy_metrics": {
      "precision": 0.89,
      "recall": 0.84,
      "f1_score": 0.86
    },
    "threshold_performance": {
      "0.8-1.0": {"accuracy": 0.95, "count": 150},
      "0.6-0.8": {"accuracy": 0.78, "count": 89}
    }
  }
}
```

### Frontend State Management

```javascript
// Redux slices cần update
const moderationSlice = {
  autoMarkedReviews: [],
  analytics: {},
  thresholdConfig: {},
  learningMetrics: {},
};
```

## 📈 Success Metrics

1. **Accuracy Improvement**: Target 5-10% improvement trong 2-4 tuần
2. **Moderator Efficiency**: Giảm 20-30% thời gian review manual
3. **False Positive Rate**: Target < 10% cho auto-marked reviews
4. **System Adoption**: > 80% moderators sử dụng new features

## 🔄 Deployment Strategy

### Phase Rollout

1. **Week 1**: Backend infrastructure + basic API
2. **Week 2**: Frontend auto-marked tab + basic analytics
3. **Week 3**: Learning algorithm + threshold configuration
4. **Week 4**: Full analytics dashboard + optimization

### Rollback Plan

- Feature flags để enable/disable từng component
- Database migration rollback scripts
- Frontend component toggling via admin settings

## 📝 Documentation Requirements

1. **API Documentation**: Update OpenAPI specs
2. **User Guide**: Moderator workflow documentation
3. **Admin Guide**: Configuration và best practices
4. **Technical Docs**: Architecture và maintenance guide

---

**Ready để bắt đầu implementation!** 🚀

Bước tiếp theo: Triển khai ModerationConfig model và database migrations.
