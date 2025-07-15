# Phân tích report.title trong ReportsList

## Vấn đề được phát hiện

Trong component `ReportsList.jsx`, dòng 293-294 có sử dụng `report.title`:

```jsx
Review: {
  report.title || "Không có tiêu đề";
}
```

## Nguồn gốc của report.title

### 1. API Endpoint

- **Endpoint**: `/api/review-reports/reports_for_moderation/`
- **Method**: GET
- **File**: `backend/apps/movies/views.py` - class `ReviewReportViewSet`

### 2. Cấu trúc Data

API `reports_for_moderation` trả về danh sách các `MovieReview` objects (không phải `ReviewReport` objects) với thêm field `report_summary`.

```python
# Trong views.py - reports_for_moderation method
serializer = MovieReviewSerializer(paginated_reviews, many=True, context={'request': request})
```

### 3. Model Structure

- **Model**: `MovieReview` (không phải `ReviewReport`)
- **Field**: `title` - CharField(max_length=255, blank=True, null=True)
- **File**: `backend/apps/movies/models.py` dòng 614

### 4. Serializer

- **Serializer**: `MovieReviewSerializer`
- **File**: `backend/apps/movies/serializers.py` dòng 455
- **Fields**: Bao gồm `title` trong danh sách fields

## Vấn đề và Giải pháp

### Vấn đề

- Field `title` trong `MovieReview` là optional (có thể null/blank)
- Khi `title` không có, hiển thị "Không có tiêu đề" không cung cấp thông tin hữu ích

### Giải pháp đã áp dụng

Thay vì hiển thị "Không có tiêu đề", sử dụng thông tin movie để tạo title có ý nghĩa:

```jsx
// Trước
Review: {
  report.title || "Không có tiêu đề";
}

// Sau
Review: {
  report.title || `Review cho ${report.movie?.title || "Phim không xác định"}`;
}
```

## Cấu trúc Data đầy đủ

### MovieReview Object (report)

```javascript
{
  id: number,
  title: string | null,           // ← Đây là report.title
  content: string,
  movie: {
    id: number,
    title: string,
    // ... other movie fields
  },
  user: {
    id: number,
    username: string,
    // ... other user fields
  },
  report_summary: {
    total_reports: number,
    unique_reasons: string[],
    reporters: string[],
    latest_report: string,
    priority: 'high' | 'medium' | 'low'
  }
  // ... other fields
}
```

### ReviewReport Object (thực tế không được sử dụng trong API này)

```javascript
{
  id: number,
  review: number,  // Review ID
  reported_by: number,  // User ID
  reason: string,
  description: string,
  created_at: string
}
```

## Kết luận

- `report.title` thực chất là `review.title` từ model `MovieReview`
- API `reports_for_moderation` trả về `MovieReview` objects, không phải `ReviewReport` objects
- Cải thiện hiển thị bằng cách sử dụng movie title khi review title không có
- Điều này cung cấp thông tin hữu ích hơn cho moderator
