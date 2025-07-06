# Cải thiện API - Bổ sung Movie Details cho Reports

## Vấn đề ban đầu

API `/api/review-reports/reports_for_moderation/` trả về `MovieReview` objects nhưng field `movie` chỉ chứa ID của phim, không có thông tin chi tiết như title, poster, genres, etc.

## Giải pháp đã áp dụng

### 1. Cải thiện MovieReviewSerializer

**File**: `backend/apps/movies/serializers.py`

Thêm `MovieSerializer` vào `MovieReviewSerializer` để trả về đầy đủ thông tin phim:

```python
class MovieReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieReview model
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)  # Include full movie details
    # ... other fields
```

### 2. Cải thiện Query Performance

**File**: `backend/apps/movies/views.py`

Thêm `prefetch_related` để tránh N+1 query cho genres:

```python
# Base queryset
queryset = ReviewReport.objects.select_related(
    'review', 'reported_by', 'review__user', 'review__movie'
).prefetch_related(
    'review__movie__genres'
).order_by('-created_at')
```

### 3. MovieSerializer Structure

**File**: `backend/apps/movies/serializers.py`

`MovieSerializer` trả về các fields sau:

```python
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'title_en', 'title_vi', 'original_title',
            'overview_en', 'overview_vi', 'release_date', 'poster_url',
            'backdrop_url', 'runtime', 'status', 'genres', 'created_at',
            'updated_at', 'is_popular', 'is_top_rated', 'is_upcoming'
        ]
```

## Cấu trúc Response mới

### Trước khi cải thiện:

```json
{
  "id": 123,
  "movie": 456, // Chỉ có ID
  "title": "Review title",
  "content": "Review content...",
  "user": {
    "id": 789,
    "username": "user123"
  }
}
```

### Sau khi cải thiện:

```json
{
  "id": 123,
  "movie": {
    "id": 456,
    "title": "Avengers: Endgame",
    "title_en": "Avengers: Endgame",
    "title_vi": "Biệt Đội Siêu Anh Hùng: Hồi Kết",
    "original_title": "Avengers: Endgame",
    "overview_en": "After the devastating events of Avengers: Infinity War...",
    "overview_vi": "Sau những sự kiện tàn khốc của Avengers: Infinity War...",
    "release_date": "2019-04-26",
    "poster_url": "https://example.com/poster.jpg",
    "backdrop_url": "https://example.com/backdrop.jpg",
    "runtime": 181,
    "status": "RELEASED",
    "genres": [
      {
        "id": 28,
        "name": "Action"
      },
      {
        "id": 12,
        "name": "Adventure"
      }
    ],
    "is_popular": true,
    "is_top_rated": true,
    "is_upcoming": false
  },
  "title": "Review title",
  "content": "Review content...",
  "user": {
    "id": 789,
    "username": "user123",
    "email": "user@example.com",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "report_summary": {
    "total_reports": 3,
    "unique_reasons": ["offensive", "spam"],
    "reporters": ["user1", "user2", "user3"],
    "priority": "high",
    "latest_report": "2024-01-15T10:30:00Z"
  }
}
```

## Lợi ích

### 1. **Thông tin đầy đủ**

- Moderator có thể thấy tên phim bằng nhiều ngôn ngữ
- Có poster và backdrop để nhận diện nhanh
- Thông tin genres để phân loại
- Release date để đánh giá context

### 2. **Performance tối ưu**

- Sử dụng `select_related` và `prefetch_related` để tránh N+1 queries
- Load tất cả dữ liệu cần thiết trong một lần query

### 3. **UX tốt hơn**

- Frontend có thể hiển thị poster phim
- Có thể tạo link trực tiếp đến trang phim
- Hiển thị genres để moderator hiểu context

### 4. **Đa ngôn ngữ**

- Hỗ trợ title bằng tiếng Anh và tiếng Việt
- Overview bằng cả hai ngôn ngữ

## Test Script

Tạo file `test_reports_api.py` để test API:

```bash
python test_reports_api.py
```

Script này sẽ:

- Test API endpoint
- Hiển thị cấu trúc response
- Kiểm tra movie details
- Validate performance

## Các fields Movie được trả về

| Field            | Type    | Description                   |
| ---------------- | ------- | ----------------------------- |
| `id`             | integer | Movie ID                      |
| `title`          | string  | Default title                 |
| `title_en`       | string  | English title                 |
| `title_vi`       | string  | Vietnamese title              |
| `original_title` | string  | Original language title       |
| `overview_en`    | string  | English overview              |
| `overview_vi`    | string  | Vietnamese overview           |
| `release_date`   | date    | Movie release date            |
| `poster_url`     | string  | Poster image URL              |
| `backdrop_url`   | string  | Backdrop image URL            |
| `runtime`        | integer | Movie duration in minutes     |
| `status`         | string  | Movie status (RELEASED, etc.) |
| `genres`         | array   | List of genre objects         |
| `is_popular`     | boolean | Popular movie flag            |
| `is_top_rated`   | boolean | Top rated movie flag          |
| `is_upcoming`    | boolean | Upcoming movie flag           |

## Kết luận

Cải thiện này giúp:

- Moderator có đầy đủ context về phim khi xử lý báo cáo
- Frontend có thể hiển thị thông tin phong phú hơn
- Performance được tối ưu với proper query optimization
- Hỗ trợ đa ngôn ngữ tốt hơn
