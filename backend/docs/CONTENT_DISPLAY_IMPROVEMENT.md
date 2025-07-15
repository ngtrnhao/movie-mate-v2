# Cải thiện hiển thị nội dung trong ReportsList

## Vấn đề ban đầu

Trong component `ReportsList.jsx`, nội dung review chỉ hiển thị 200 ký tự đầu và bị cắt ngắn:

```jsx
<strong>Nội dung:</strong> {report.content?.substring(0, 200)}...
```

Điều này không cho phép moderator xem toàn bộ nội dung để đánh giá chính xác.

## Giải pháp đã áp dụng

### 1. Hiển thị toàn bộ nội dung với toggle

**Thêm state để quản lý việc mở rộng nội dung:**

```jsx
const [expandedContent, setExpandedContent] = useState(new Set());
```

**Thêm functions để toggle hiển thị:**

```jsx
const toggleContentExpansion = (reportId) => {
  setExpandedContent((prev) => {
    const newSet = new Set(prev);
    if (newSet.has(reportId)) {
      newSet.delete(reportId);
    } else {
      newSet.add(reportId);
    }
    return newSet;
  });
};

const isContentExpanded = (reportId) => {
  return expandedContent.has(reportId);
};
```

### 2. Cải thiện UI hiển thị

**Trước:**

```jsx
<p className="mb-1">
  <strong>Nội dung:</strong> {report.content?.substring(0, 200)}...
</p>
```

**Sau:**

```jsx
<div className="mb-2">
  <strong>Nội dung:</strong>
  <div className="mt-1 p-3 bg-gray-50 rounded-lg whitespace-pre-wrap text-gray-700">
    {isContentExpanded(report.id)
      ? report.content || "Không có nội dung"
      : report.content?.length > 300
      ? `${report.content.substring(0, 300)}...`
      : report.content || "Không có nội dung"}
  </div>
  {report.content && report.content.length > 300 && (
    <button
      onClick={() => toggleContentExpansion(report.id)}
      className="mt-2 text-blue-600 hover:text-blue-800 text-xs font-medium"
    >
      {isContentExpanded(report.id) ? "Thu gọn" : "Xem thêm"}
    </button>
  )}
</div>
```

## Tính năng mới

### 1. **Hiển thị thông minh**

- Nội dung ngắn (< 300 ký tự): Hiển thị toàn bộ
- Nội dung dài (> 300 ký tự): Hiển thị 300 ký tự đầu + nút "Xem thêm"

### 2. **Toggle button**

- **"Xem thêm"**: Mở rộng để xem toàn bộ nội dung
- **"Thu gọn"**: Thu gọn lại về 300 ký tự đầu

### 3. **Styling cải thiện**

- Background màu xám nhạt (`bg-gray-50`)
- Padding và border radius để dễ đọc
- `whitespace-pre-wrap` để giữ nguyên format xuống dòng
- Text color tối hơn để dễ đọc

### 4. **State management**

- Sử dụng `Set` để track các review đã mở rộng
- Mỗi review có thể mở rộng/thu gọn độc lập
- State được reset khi component re-render

## Ví dụ hiển thị

### Nội dung ngắn (< 300 ký tự):

```
Nội dung:
┌─────────────────────────────────────┐
│ Phim rất hay, diễn viên xuất sắc!   │
│ Đáng xem.                           │
└─────────────────────────────────────┘
```

### Nội dung dài (> 300 ký tự) - Thu gọn:

```
Nội dung:
┌─────────────────────────────────────┐
│ Phim rất hay, diễn viên xuất sắc!   │
│ Đáng xem. Nội dung rất chi tiết...  │
└─────────────────────────────────────┘
[Xem thêm]
```

### Nội dung dài (> 300 ký tự) - Mở rộng:

```
Nội dung:
┌─────────────────────────────────────┐
│ Phim rất hay, diễn viên xuất sắc!   │
│ Đáng xem. Nội dung rất chi tiết     │
│ và đầy đủ thông tin về cốt truyện,  │
│ nhân vật, và các tình tiết trong    │
│ phim. Đây là một tác phẩm nghệ      │
│ thuật xuất sắc!                     │
└─────────────────────────────────────┘
[Thu gọn]
```

## Lợi ích

### 1. **UX tốt hơn**

- Moderator có thể xem toàn bộ nội dung khi cần
- Giao diện gọn gàng với nội dung dài
- Dễ dàng toggle giữa xem rút gọn và đầy đủ

### 2. **Performance**

- Không load toàn bộ nội dung dài ngay lập tức
- Chỉ mở rộng khi user cần xem

### 3. **Accessibility**

- Button có hover state rõ ràng
- Text contrast tốt để dễ đọc
- Responsive design

### 4. **Maintainability**

- Code sạch và dễ hiểu
- State management rõ ràng
- Dễ dàng thay đổi threshold (300 ký tự)

## Cấu hình có thể tùy chỉnh

- **Threshold**: Có thể thay đổi từ 300 ký tự thành giá trị khác
- **Button text**: Có thể thay đổi "Xem thêm"/"Thu gọn" thành text khác
- **Styling**: Có thể tùy chỉnh màu sắc, padding, border radius
- **Animation**: Có thể thêm transition effects

## Kết luận

Cải thiện này giúp moderator:

- Xem toàn bộ nội dung review khi cần thiết
- Có giao diện gọn gàng và dễ sử dụng
- Đưa ra quyết định chính xác hơn dựa trên nội dung đầy đủ
- Tăng hiệu quả trong việc kiểm duyệt nội dung
