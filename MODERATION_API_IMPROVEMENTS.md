# Moderation Queue API Improvements

## Tổng quan

Đã cải tiến API `/api/reviews/moderation_queue/` để bao gồm thông tin movie đầy đủ thay vì chỉ trả về movie ID. Điều này giúp frontend hiển thị tên phim mà không cần gọi thêm API.

## Những thay đổi đã thực hiện

### 1. Backend Changes

#### A. Tạo Serializer mới

**File:** `backend/apps/movies/serializers.py`

Thêm `ModerationQueueReviewSerializer` mới:

```python
class ModerationQueueReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for moderation queue with full movie details
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)  # Include full movie details
    reviewer_name = serializers.CharField(read_only=True)
    reviewer_avatar = serializers.CharField(read_only=True)
    is_verified_reviewer = serializers.BooleanField(read_only=True)
    helpfulness_ratio = serializers.SerializerMethodField()
    moderation_analysis = serializers.SerializerMethodField()
    report_summary = serializers.SerializerMethodField()

    # ... implementation details
```

#### B. Cập nhật Views

**File:** `backend/apps/movies/views.py`

1. **Import serializer mới:**

```python
from .serializers import (..., ModerationQueueReviewSerializer)
```

2. **Cập nhật moderation_queue view:**

```python
serializer = ModerationQueueReviewSerializer(paginated_reviews, many=True, context={'request': request})
```

3. **Cập nhật unified_moderation_queue view:**

```python
# Use the new serializer for full movie details
serializer = ModerationQueueReviewSerializer(review, context={'request': request})
task['review_data'] = serializer.data
```

### 2. Frontend Changes

#### A. Cập nhật ContentModerationDashboard

**File:** `frontend/src/pages/Moderator/components/ContentModerationDashboard.jsx`

1. **Cập nhật grouping logic:**

```javascript
// Before
const groupedReviews = {
  high: reviews.filter((r) => r.spoiler_analysis?.priority_level === "high"),
  // ...
};

// After
const groupedReviews = {
  high: reviews.filter((r) => r.moderation_analysis?.priority_level === "high"),
  // ...
};
```

2. **Cập nhật ReviewCard component:**

```javascript
// Before
{review.spoiler_analysis && (
  <span className={...}>
    {Math.round(review.spoiler_analysis.confidence * 100)}%
  </span>
)}

// After
{review.moderation_analysis && (
  <span className={...}>
    {review.moderation_analysis.spoiler_analysis
      ? Math.round(review.moderation_analysis.spoiler_analysis.confidence * 100)
      : review.moderation_analysis.priority_level === 'high' ? 'Cao' : 'TB' : 'Thấp'}%
  </span>
)}
```

3. **Cập nhật List View:**

```javascript
// Before
{review.spoiler_analysis && (
  <span className={...}>
    {review.spoiler_analysis.priority_level === 'high' ? 'Ưu tiên cao' : ...}
  </span>
)}

// After
{review.moderation_analysis && (
  <span className={...}>
    {review.moderation_analysis.priority_level === 'high' ? 'Ưu tiên cao' : ...}
  </span>
)}
```

4. **Cập nhật Modal:**

```javascript
// Before
{(spoilerResult || selectedReview?.spoiler_analysis) && (

// After
{(spoilerResult || selectedReview?.moderation_analysis?.spoiler_analysis) && (
```

## Response Format

### Before (Chỉ movie ID)

```json
{
  "id": 11558,
  "movie": 441891,  // Chỉ có ID
  "user": {...},
  "content": "...",
  // ...
}
```

### After (Full movie details)

```json
{
  "id": 11558,
  "movie": {
    "id": 441891,
    "title": "Lilo & Stitch",
    "slug": "lilo-stitch",
    "poster_url": "...",
    "backdrop_url": "...",
    "overview_en": "...",
    "overview_vi": "...",
    // ... full movie details
  },
  "user": {...},
  "content": "...",
  "moderation_analysis": {
    "priority_level": "medium",
    "moderation_reasons": ["potential_spoiler"],
    "spoiler_analysis": {
      "is_spoiler": false,
      "confidence": 0.572,
      "detected_patterns": [...],
      "spoiler_indicators": [...],
      "explanation": "..."
    }
  }
  // ...
}
```

## Testing

### 1. Test Script

Sử dụng file `test_moderation_api.py` để test API:

```bash
# Cài đặt dependencies
pip install requests

# Chạy test
python test_moderation_api.py
```

### 2. Postman Testing

#### Basic Request:

```
GET http://localhost:8000/api/reviews/moderation_queue/
Headers: Authorization: Bearer <your_jwt_token>
```

#### With Filters:

```
GET http://localhost:8000/api/reviews/moderation_queue/?priority=high&language=en&page=1&page_size=20
Headers: Authorization: Bearer <your_jwt_token>
```

### 3. Expected Results

✅ **Success Cases:**

- API trả về 200 OK với full movie details
- Movie object chứa title, poster_url, overview, etc.
- Moderation analysis được bao gồm
- Pagination hoạt động đúng

❌ **Error Cases:**

- 401 Unauthorized: Không có token
- 403 Forbidden: User không có quyền moderator/admin
- 500 Internal Server Error: Lỗi server

## Benefits

1. **Performance:** Giảm số lượng API calls từ frontend
2. **UX:** Hiển thị tên phim ngay lập tức không cần loading
3. **Consistency:** Đảm bảo thông tin movie luôn đồng bộ
4. **Maintainability:** Code dễ maintain hơn với serializer riêng biệt

## Migration Notes

- **Backward Compatibility:** API vẫn tương thích với frontend cũ
- **Database:** Không cần thay đổi database schema
- **Deployment:** Chỉ cần restart Django server sau khi deploy

## Future Improvements

1. **Caching:** Thêm Redis cache cho movie details
2. **Optimization:** Sử dụng select_related/prefetch_related tốt hơn
3. **Pagination:** Cải thiện pagination performance
4. **Filtering:** Thêm filters cho movie title, genre, etc.
