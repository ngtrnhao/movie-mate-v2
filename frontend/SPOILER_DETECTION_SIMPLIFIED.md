# Hệ thống Spoiler Detection Đơn giản hóa

## Tổng quan

Hệ thống spoiler detection đã được đơn giản hóa để chạy ngầm và chỉ hiển thị thông báo khi cần thiết.

## Cách hoạt động

### 1. Phân tích ngầm
- Hệ thống tự động phân tích nội dung review khi người dùng nhập
- Không hiển thị tiến trình phân tích hay kết quả trung gian
- Chạy hoàn toàn trong nền

### 2. Phân loại review

#### Auto Approve (0-40% confidence)
- Review được tự động phê duyệt
- Không hiển thị thông báo gì
- Không đánh dấu spoiler

#### User Confirmation (60-80% confidence)
- Hiển thị thông báo yêu cầu xác nhận từ người dùng
- Người dùng có thể chọn đánh dấu spoiler hoặc bỏ qua
- Review vẫn được gửi bình thường

#### Moderation Required (40-60% confidence)
- Review được gửi đến dashboard của Moderator
- Hiển thị thông báo ngắn (5 giây) rồi tự động ẩn
- Không làm gián đoạn trải nghiệm người dùng

#### Auto Mark Spoiler (80%+ confidence)
- Tự động đánh dấu review là spoiler
- Không hiển thị thông báo
- Review được gửi bình thường

## Components

### 1. useSpoilerDetection Hook
```javascript
const {
  isAnalyzing,
  detectionResult,
  error,
  analyzeContentDebounced,
  clearAnalysis,
  shouldAutoMark,
  shouldShowWarning,
  getAdvancedClassification,
} = useSpoilerDetection('vi', movieTitle);
```

### 2. SpoilerDetectionAlert
- Chỉ hiển thị khi cần xác nhận từ người dùng
- Đơn giản hóa, không có progress bar hay intermediate results

### 3. ModerationNotification
- Thông báo ngắn khi review được gửi đến moderation
- Tự động ẩn sau 5 giây

### 4. SpoilerBadge
- Hiển thị badge "Spoiler" trên các review đã đánh dấu

## Tích hợp trong RatingTab

```javascript
// Chỉ hiển thị alert khi cần xác nhận
{reviewClassification?.action === 'user_confirmation' && detectionResult && (
  <SpoilerDetectionAlert
    detectionResult={detectionResult}
    isAnalyzing={isAnalyzing}
    onMarkAsSpoiler={() => setIsSpoiler(true)}
    onDismiss={clearAnalysis}
  />
)}

// Thông báo moderation tự động ẩn
{showModerationNotification && reviewClassification?.action === 'moderation_required' && (
  <ModerationNotification
    classification={reviewClassification}
    onDismiss={() => setShowModerationNotification(false)}
  />
)}
```

## Lợi ích

1. **Trải nghiệm người dùng tốt hơn**: Không bị gián đoạn bởi các thông báo không cần thiết
2. **Hiệu suất cao hơn**: Không có real-time progress updates
3. **Đơn giản hóa**: Chỉ hiển thị thông tin cần thiết
4. **Tự động hóa**: Hầu hết các trường hợp được xử lý tự động
5. **Moderation hiệu quả**: Review cần kiểm tra được gửi đến dashboard

## Backend Integration

- API endpoint: `/api/reviews/detect_spoilers/`
- Tự động gửi review cần moderation đến dashboard
- Không cần thay đổi logic backend

## Cấu hình

- Ngưỡng confidence có thể điều chỉnh trong hook
- Thời gian hiển thị thông báo moderation có thể thay đổi
- Ngôn ngữ hỗ trợ: Tiếng Việt và Tiếng Anh
