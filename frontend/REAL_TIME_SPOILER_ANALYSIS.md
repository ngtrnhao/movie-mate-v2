# Real-time Spoiler Analysis Feature

## Tổng quan

Tính năng phân tích spoiler theo thời gian thực đã được cải tiến để cung cấp trải nghiệm người dùng tốt hơn với kết quả phân tích từng phần thay vì phải đợi toàn bộ quá trình hoàn thành. Tính năng này hiện được tích hợp vào **RatingTab** - nơi người dùng đánh giá và viết review về phim.

## Các tính năng mới

### 1. Phân tích từng phần (Progressive Analysis)

Hệ thống hiện tại thực hiện phân tích theo 3 giai đoạn:

#### Giai đoạn 1: Phân tích từ khóa (0-30%)

- **Thời gian**: Ngay lập tức
- **Mô tả**: Tìm kiếm các từ khóa spoiler cơ bản
- **Từ khóa tiếng Việt**: `kết thúc`, `chết`, `cưới`, `phản bội`, `bí mật`, `twist`, `spoiler`, `cuối phim`, `hóa ra`, `sự thật`
- **Từ khóa tiếng Anh**: `ending`, `dies`, `marries`, `betrayal`, `secret`, `twist`, `spoiler`, `end of movie`, `turns out`, `truth`

#### Giai đoạn 2: Phân tích mẫu câu (30-60%)

- **Thời gian**: 300ms sau giai đoạn 1
- **Mô tả**: Kiểm tra các mẫu câu có thể chứa spoiler
- **Mẫu câu tiếng Việt**: `sẽ`, `hóa ra`, `sự thật là`, `scene`
- **Mẫu câu tiếng Anh**: `will`, `turns out`, `truth is`, `scene`

#### Giai đoạn 3: Phân tích ngữ cảnh (60-85%)

- **Thời gian**: 600ms sau giai đoạn 1
- **Mô tả**: Đánh giá ngữ cảnh và ý nghĩa
- **Chỉ báo ngữ cảnh**: `review`, `đánh giá`, `cinematography`, `acting`, `direction`

#### Giai đoạn 4: Phân tích toàn diện (85-100%)

- **Thời gian**: 900ms sau giai đoạn 1
- **Mô tả**: Gọi API backend để phân tích chính xác
- **Kết quả**: Kết quả cuối cùng với độ tin cậy cao

### 2. Hiển thị tiến trình real-time

#### Component: `SpoilerDetectionAlert`

- Hiển thị giai đoạn phân tích hiện tại
- Progress bar với animation mượt mà
- Kết quả tạm thời trong quá trình phân tích
- Icon thay đổi theo giai đoạn phân tích

#### Component: `SpoilerAnalysisStats`

- Thống kê chi tiết về quá trình phân tích
- Hiển thị các dấu hiệu được phát hiện
- Độ tin cậy theo thời gian thực
- Mẹo phân tích cho người dùng

### 3. Cải tiến UX

#### Debounce tối ưu

- Giảm thời gian debounce từ 1000ms xuống 500ms
- Phản hồi nhanh hơn khi người dùng gõ

#### Kết quả tạm thời

- Hiển thị kết quả ngay khi có dữ liệu
- Không cần đợi toàn bộ quá trình hoàn thành
- Cập nhật liên tục theo tiến trình phân tích

#### Visual Feedback

- Progress bar với màu sắc thay đổi theo giai đoạn
- Icon animation cho từng giai đoạn
- Thông báo trạng thái rõ ràng

## Cấu trúc code

### Hook: `useSpoilerDetection`

```javascript
const {
  // State
  isAnalyzing,
  detectionResult,
  error,
  analysisProgress,
  intermediateResults,

  // Actions
  analyzeContent,
  analyzeContentDebounced,
  clearAnalysis,

  // Utilities
  getCurrentResult,
  getRecommendationColor,
  getRecommendationIcon,
  getRecommendationMessage,

  // Computed values
  isSpoiler,
  confidence,
  shouldShowWarning,
  shouldAutoMark,
} = useSpoilerDetection(language, movieTitle);
```

### Các hàm phân tích

#### `performQuickAnalysis(content, language)`

- Phân tích từ khóa cơ bản
- Trả về kết quả ngay lập tức
- Độ tin cậy dựa trên số lượng từ khóa tìm thấy

#### `performPatternAnalysis(content, language)`

- Phân tích mẫu câu phức tạp
- Sử dụng regex patterns
- Tính điểm dựa trên trọng số

#### `performContextAnalysis(content, language, movieTitle)`

- Phân tích ngữ cảnh
- Đánh giá chỉ báo đánh giá
- Điều chỉnh điểm số dựa trên ngữ cảnh

## Sử dụng

### Trong RatingTab

```javascript
// Trigger phân tích khi người dùng gõ
onChange={e => {
  const newContent = e.target.value;
  setRatingComment(newContent);

  if (newContent.trim().length >= 10) {
    analyzeContentDebounced(newContent);
  } else {
    clearAnalysis();
  }
}}

// Hiển thị kết quả
<SpoilerDetectionAlert
  detectionResult={detectionResult}
  isAnalyzing={isAnalyzing}
  analysisProgress={analysisProgress}
  intermediateResults={intermediateResults}
  onMarkAsSpoiler={() => setIsSpoiler(true)}
  onDismiss={clearAnalysis}
/>

<SpoilerAnalysisStats
  analysisProgress={analysisProgress}
  intermediateResults={intermediateResults}
  detectionResult={detectionResult}
  isAnalyzing={isAnalyzing}
/>
```

## Lợi ích

### 1. Trải nghiệm người dùng tốt hơn

- Không cần đợi lâu để có kết quả
- Phản hồi ngay lập tức khi gõ
- Hiểu rõ quá trình phân tích

### 2. Hiệu suất cải thiện

- Giảm thời gian chờ
- Phân tích từng phần hiệu quả
- Tối ưu hóa API calls

### 3. Độ chính xác cao hơn

- Kết hợp nhiều phương pháp phân tích
- Cập nhật liên tục kết quả
- Đánh giá ngữ cảnh chính xác

## Cấu hình

### Thời gian phân tích

```javascript
// Có thể điều chỉnh trong useSpoilerDetection.js
setTimeout(() => {
  // Pattern analysis
}, 300);

setTimeout(() => {
  // Context analysis
}, 600);

setTimeout(() => {
  // Final analysis
}, 900);
```

### Từ khóa và mẫu câu

```javascript
// Có thể mở rộng trong các hàm phân tích
const keywords = ['kết thúc', 'chết', 'cưới', ...];
const patterns = [
  { pattern: /\b(sẽ|will)\b/g, weight: 0.1 },
  { pattern: /\b(hóa ra|turns out)\b/g, weight: 0.2 },
  // ...
];
```

## Troubleshooting

### Vấn đề thường gặp

1. **Phân tích không hoạt động**

   - Kiểm tra độ dài nội dung (tối thiểu 10 ký tự)
   - Kiểm tra kết nối API
   - Xem console logs

2. **Kết quả không chính xác**

   - Cập nhật từ khóa và mẫu câu
   - Điều chỉnh trọng số phân tích
   - Kiểm tra ngữ cảnh ngôn ngữ

3. **Performance issues**
   - Giảm thời gian debounce
   - Tối ưu hóa regex patterns
   - Giới hạn số lượng API calls

### Debug

```javascript
// Thêm debug logs
console.log('Analysis progress:', analysisProgress);
console.log('Intermediate results:', intermediateResults);
console.log('Final result:', detectionResult);
```

## Tương lai

### Cải tiến dự kiến

1. **Machine Learning Integration**

   - Sử dụng ML models cho phân tích chính xác hơn
   - Training với dataset lớn hơn
   - Cải thiện độ chính xác

2. **Multi-language Support**

   - Hỗ trợ thêm ngôn ngữ
   - Phân tích đa ngôn ngữ
   - Context-aware language detection

3. **Advanced Patterns**

   - Phân tích sentiment
   - Named entity recognition
   - Semantic analysis

4. **Real-time Collaboration**
   - Chia sẻ kết quả phân tích
   - Collaborative spoiler detection
   - Community feedback system
