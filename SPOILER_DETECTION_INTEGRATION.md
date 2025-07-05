# Spoiler Detection Integration - Tài liệu tích hợp

## Tổng quan

Hệ thống phát hiện spoiler đã được tích hợp hoàn chỉnh vào ứng dụng Movie Mate, bao gồm cả backend và frontend.

## Backend Components

### 1. SpoilerDetectionService

**File:** `backend/apps/movies/services/spoiler_detection_service.py`

**Chức năng:**

- Phát hiện spoiler dựa trên từ khóa tiếng Việt và tiếng Anh
- Phân tích mẫu câu và ngữ cảnh
- Tính toán độ tin cậy (confidence score)
- Đưa ra gợi ý hành động

**Phương thức chính:**

```python
def detect_spoilers(content: str, language: str = 'en', movie_title: str = None) -> SpoilerDetectionResult
```

### 2. API Endpoints

**File:** `backend/apps/movies/views.py`

**Endpoints:**

- `POST /reviews/detect_spoilers/` - Phát hiện spoiler trong nội dung
- `POST /reviews/{id}/analyze_spoiler/` - Phân tích review hiện có
- `GET /reviews/spoiler_statistics/` - Thống kê spoiler detection

**Tích hợp tự động:**

- Tự động đánh dấu spoiler khi `confidence > 0.8`
- Gửi thông tin detection trong response khi tạo/cập nhật review

## Frontend Components

### 1. API Service

**File:** `frontend/src/api/movieService.js`

**Methods:**

```javascript
detectSpoilers(content, language, movieTitle);
analyzeReviewSpoiler(reviewId);
getSpoilerStatistics();
submitMovieReviewWithSpoilerDetection(movieId, reviewData);
```

### 2. Custom Hook

**File:** `frontend/src/hooks/useSpoilerDetection.js`

**Chức năng:**

- Real-time spoiler detection với debounce
- Quản lý state và error handling
- Utility functions cho UI

### 3. UI Components

#### SpoilerDetectionAlert

**File:** `frontend/src/components/common/SpoilerDetectionAlert.jsx`

**Chức năng:**

- Hiển thị cảnh báo spoiler với các mức độ khác nhau
- Progress bar độ tin cậy
- Action buttons (đánh dấu spoiler, xem lại nội dung)
- Responsive design

#### SpoilerBadge

**File:** `frontend/src/components/common/SpoilerBadge.jsx`

**Chức năng:**

- Badge hiển thị spoiler cho review đã có
- Multiple sizes và variants
- Consistent styling

## Tích hợp vào các Form Review

### 1. RatingTab (Movie Detail)

**File:** `frontend/src/pages/Movies/components/RatingTab.jsx`

**Tính năng:**

- ✅ Real-time spoiler detection khi nhập review
- ✅ SpoilerDetectionAlert với gợi ý
- ✅ Checkbox "Chứa spoiler"
- ✅ Tự động đánh dấu khi confidence cao
- ✅ Gửi trường `is_spoiler` khi submit

### 2. CommentTab (Movie Detail)

**File:** `frontend/src/pages/Movies/components/CommentTab.jsx`

**Tính năng:**

- ✅ Real-time spoiler detection khi nhập comment
- ✅ SpoilerDetectionAlert với gợi ý
- ✅ Checkbox "Chứa spoiler"
- ✅ Tự động đánh dấu khi confidence cao
- ✅ Gửi trường `is_spoiler` khi submit

### 3. ReplySection

**File:** `frontend/src/components/common/ReplySection.jsx`

**Tính năng:**

- ✅ Real-time spoiler detection khi nhập reply
- ✅ SpoilerDetectionAlert với gợi ý
- ✅ Checkbox "Chứa spoiler"
- ✅ Tự động đánh dấu khi confidence cao
- ✅ Gửi trường `is_spoiler` khi submit

## Hiển thị Review có Spoiler

### 1. RatingTab & CommentTab

- ✅ SpoilerBadge hiển thị bên cạnh tên user
- ✅ Blur content mặc định (có thể toggle)
- ✅ "Nhấn để xem spoiler" button

### 2. Profile - RatingList

**File:** `frontend/src/pages/Profile/components/RatingList.jsx`

**Tính năng:**

- ✅ SpoilerBadge cho grid view và list view
- ✅ Hiển thị badge với kích thước phù hợp

### 3. Moderator Dashboard

**File:** `frontend/src/pages/Moderator/components/SpoilerDetectionPanel.jsx`

**Tính năng:**

- ✅ Thống kê spoiler detection
- ✅ Phân tích mẫu phát hiện phổ biến
- ✅ Quick actions cho moderator

## Luồng hoạt động

### 1. Khi user nhập review:

1. User nhập nội dung vào textarea
2. Hook `useSpoilerDetection` gọi API sau 1 giây debounce
3. Hiển thị `SpoilerDetectionAlert` với kết quả
4. User có thể:
   - Đánh dấu spoiler thủ công
   - Để hệ thống tự động đánh dấu (nếu confidence > 0.8)
   - Xem lại nội dung

### 2. Khi submit review:

1. Gửi trường `is_spoiler` lên backend
2. Backend chạy detection một lần nữa
3. Tự động đánh dấu nếu confidence cao
4. Trả về thông tin detection trong response

### 3. Khi hiển thị review:

1. Kiểm tra trường `is_spoiler`
2. Hiển thị `SpoilerBadge` nếu có
3. Blur content mặc định (có thể toggle)

## Cấu hình và Tùy chỉnh

### 1. Ngôn ngữ hỗ trợ:

- Tiếng Việt (vi)
- Tiếng Anh (en)

### 2. Độ tin cậy:

- **High (> 0.8)**: Tự động đánh dấu spoiler
- **Medium (0.6-0.8)**: Gợi ý đánh dấu
- **Low (0.4-0.6)**: Cảnh báo kiểm tra
- **Safe (< 0.4)**: Không có dấu hiệu spoiler

### 3. Keywords và Patterns:

- High confidence: kết thúc, chết, twist, reveal, etc.
- Medium confidence: nhân vật, tình tiết, quan hệ, etc.
- Low confidence: diễn xuất, âm nhạc, hiệu ứng, etc.

## Testing

### 1. Test Cases:

```javascript
// High confidence spoiler
"Phim kết thúc với cái chết của nhân vật chính";

// Medium confidence
"Tình tiết phát triển nhân vật rất hay";

// Low confidence
"Diễn xuất và âm nhạc rất xuất sắc";

// Safe content
"Phim có hình ảnh đẹp và nhạc nền hay";
```

### 2. Manual Testing:

- Nhập các loại nội dung khác nhau
- Kiểm tra độ chính xác của detection
- Test UI responsiveness
- Verify spoiler badge hiển thị đúng

## Kết luận

Hệ thống spoiler detection đã được tích hợp hoàn chỉnh với:

- ✅ Backend service mạnh mẽ
- ✅ Frontend UI thân thiện
- ✅ Real-time detection
- ✅ Consistent styling
- ✅ Comprehensive coverage

Tất cả các form review và nơi hiển thị review đều đã được tích hợp đầy đủ chức năng phát hiện và cảnh báo spoiler.
