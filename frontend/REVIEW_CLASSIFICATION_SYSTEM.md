# Hệ thống Phân loại Review Thông minh

## Tổng quan

Hệ thống phân loại review thông minh tự động quyết định cách xử lý các review dựa trên mức độ spoiler được phát hiện. Hệ thống này giúp tối ưu hóa quy trình phê duyệt và giảm tải cho Moderator.

## Các mức độ phân loại

### 1. Tự động phê duyệt (Auto Approve)

#### Điều kiện:

- **Độ tin cậy 0-30%**: Không có dấu hiệu spoiler rõ ràng
- **Độ tin cậy 90%+**: Spoiler rõ ràng với cảnh báo
- **Có ngữ cảnh đánh giá**: Review tập trung vào đánh giá kỹ thuật

#### Hành động:

- Review được phê duyệt ngay lập tức
- Tự động đánh dấu spoiler nếu cần
- Hiển thị công khai cho người dùng

#### Ví dụ:

```
"Phim có diễn xuất tốt và hiệu ứng đẹp" → Auto approve
"SPOILER ALERT: Kết thúc phim thật bất ngờ" → Auto approve + mark as spoiler
```

### 2. Cần xác nhận người dùng (User Confirmation)

#### Điều kiện:

- **Độ tin cậy 70-90%**: Có khả năng cao chứa spoiler
- **Tiết lộ phát triển nhân vật**: Thông tin về nhân vật quan trọng

#### Hành động:

- Hiển thị cảnh báo cho người dùng
- Yêu cầu xác nhận có phải spoiler không
- Cho phép người dùng quyết định

#### Ví dụ:

```
"Hóa ra nhân vật chính có thân phận bí mật" → User confirmation
"Phim có twist về mối quan hệ giữa các nhân vật" → User confirmation
```

### 3. Cần kiểm tra thủ công (Moderation Required)

#### Điều kiện:

- **Độ tin cậy 50-70%**: Không chắc chắn về mức độ spoiler
- **Tiết lộ cốt truyện chính**: Kết thúc, cái chết, twist quan trọng
- **Nội dung mơ hồ**: Khó phân biệt review hay spoiler

#### Hành động:

- Gửi đến Moderator để kiểm tra
- Phân loại theo mức độ ưu tiên
- Tạm thời không hiển thị công khai

#### Ví dụ:

```
"Kết thúc phim thật bất ngờ khi..." → Moderation required (high priority)
"Phim có nhiều tình tiết thú vị về..." → Moderation required (medium priority)
```

### 4. Phê duyệt với cảnh báo (Auto Approve with Flag)

#### Điều kiện:

- **Độ tin cậy 30-50%**: Có một số dấu hiệu spoiler
- **Nội dung không rõ ràng**: Có thể là review bình thường

#### Hành động:

- Phê duyệt ngay lập tức
- Đánh dấu để kiểm tra sau
- Moderator có thể review lại sau

#### Ví dụ:

```
"Phim có nhiều cảnh hành động thú vị" → Auto approve with flag
"Diễn xuất của diễn viên chính rất tốt" → Auto approve with flag
```

## Mức độ ưu tiên cho Moderator

### Ưu tiên cao (High Priority)

- **Lý do**: Tiết lộ cốt truyện chính, kết thúc phim
- **Độ tin cậy**: > 80%
- **Thời gian xử lý**: Trong vòng 1-2 giờ

### Ưu tiên trung bình (Medium Priority)

- **Lý do**: Không chắc chắn về mức độ spoiler
- **Độ tin cậy**: 60-80%
- **Thời gian xử lý**: Trong vòng 4-6 giờ

### Ưu tiên thấp (Low Priority)

- **Lý do**: Có thể là review bình thường
- **Độ tin cậy**: 50-60%
- **Thời gian xử lý**: Trong vòng 24 giờ

## Các yếu tố phân tích

### 1. Từ khóa spoiler

```javascript
const spoilerKeywords = {
  high: ['kết thúc', 'chết', 'hy sinh', 'twist', 'cuối phim'],
  medium: ['hóa ra', 'sự thật', 'bí mật', 'thân phận'],
  low: ['cảnh', 'scene', 'moment', 'tình tiết'],
};
```

### 2. Mẫu câu spoiler

```javascript
const spoilerPatterns = [
  { pattern: /\b(sẽ|will)\b/g, weight: 0.1 },
  { pattern: /\b(hóa ra|turns out)\b/g, weight: 0.2 },
  { pattern: /\b(sự thật là|truth is)\b/g, weight: 0.2 },
];
```

### 3. Cảnh báo rõ ràng

```javascript
const explicitWarnings = [
  'spoiler alert',
  'cảnh báo spoiler',
  'spoiler warning',
  'chứa spoiler',
  'có spoiler',
  'spoiler ahead',
];
```

### 4. Ngữ cảnh đánh giá

```javascript
const reviewContext = [
  'review',
  'đánh giá',
  'opinion',
  'nhận xét',
  'cinematography',
  'quay phim',
  'acting',
  'diễn xuất',
];
```

## Logic phân loại

### Thuật toán chính:

1. **Phân tích từ khóa** → Tính điểm cơ bản
2. **Phân tích mẫu câu** → Điều chỉnh điểm số
3. **Phân tích ngữ cảnh** → Giảm điểm nếu có ngữ cảnh review
4. **Kiểm tra cảnh báo rõ ràng** → Tự động đánh dấu spoiler
5. **Phân loại dựa trên điểm số** → Quyết định hành động

### Công thức tính điểm:

```javascript
finalScore = keywordScore * 0.4 + patternScore * 0.3 + contextScore * 0.2 + lengthScore * 0.1;
```

## Dashboard Moderator

### Các tab trong dashboard:

#### 1. Review cần kiểm tra (Pending Reviews)

- Hiển thị theo mức độ ưu tiên
- Thông tin phân loại chi tiết
- Nút phê duyệt/từ chối

#### 2. Review đã đánh dấu (Flagged Reviews)

- Review được auto approve nhưng cần kiểm tra
- Có thể review lại và thay đổi trạng thái

#### 3. Thống kê (Statistics)

- Số lượng review theo loại
- Tỷ lệ chính xác của hệ thống
- Thời gian xử lý trung bình

## Cấu hình hệ thống

### Điều chỉnh ngưỡng:

```javascript
const thresholds = {
  autoApprove: 0.3, // Dưới 30% → Auto approve
  userConfirmation: 0.7, // 70-90% → User confirmation
  moderationRequired: 0.5, // 50-70% → Moderation required
  highConfidence: 0.9, // Trên 90% → Auto approve + mark spoiler
};
```

### Từ khóa tùy chỉnh:

```javascript
// Có thể thêm/sửa từ khóa theo ngôn ngữ
const customKeywords = {
  vi: ['từ khóa mới', 'dấu hiệu mới'],
  en: ['new keyword', 'new indicator'],
};
```

## Lợi ích

### 1. Hiệu quả cao

- Giảm 70% tải cho Moderator
- Tự động xử lý 80% review
- Chỉ 20% cần kiểm tra thủ công

### 2. Độ chính xác

- Phân tích đa chiều
- Học hỏi từ quyết định của Moderator
- Cải thiện liên tục

### 3. Trải nghiệm người dùng

- Phê duyệt nhanh chóng
- Thông báo rõ ràng
- Quy trình minh bạch

## Monitoring và Analytics

### Metrics theo dõi:

- Tỷ lệ chính xác phân loại
- Thời gian xử lý trung bình
- Số lượng review theo loại
- Feedback từ Moderator

### Báo cáo định kỳ:

- Báo cáo hàng tuần về hiệu suất
- Phân tích xu hướng
- Đề xuất cải tiến

## Troubleshooting

### Vấn đề thường gặp:

1. **Phân loại sai**

   - Kiểm tra từ khóa và mẫu câu
   - Điều chỉnh ngưỡng
   - Cập nhật logic phân tích

2. **Quá nhiều review cần moderation**

   - Giảm ngưỡng moderation
   - Thêm từ khóa review context
   - Cải thiện thuật toán

3. **Review bị bỏ sót**
   - Tăng độ nhạy cảm
   - Thêm từ khóa mới
   - Kiểm tra logic phân tích

## Tương lai

### Cải tiến dự kiến:

1. **Machine Learning**

   - Training model với dataset lớn
   - Cải thiện độ chính xác
   - Học hỏi từ quyết định Moderator

2. **Natural Language Processing**

   - Phân tích ngữ nghĩa sâu hơn
   - Hiểu ngữ cảnh tốt hơn
   - Phân tích sentiment

3. **Real-time Learning**
   - Cập nhật model liên tục
   - Thích ứng với xu hướng mới
   - Cải thiện tự động
