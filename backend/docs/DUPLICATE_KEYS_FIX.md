# Sửa lỗi Duplicate Keys trong QueueList

## Tổng quan

Đã sửa lỗi React warning về duplicate keys trong QueueList component. Lỗi này xảy ra khi có nhiều items có cùng ID trong danh sách moderation queue.

## Nguyên nhân

1. **API trả về duplicate data**: Unified moderation queue API có thể trả về cùng một review nhiều lần với các lý do khác nhau
2. **Keys không unique**: Sử dụng chỉ `item.id` làm key không đủ để đảm bảo uniqueness
3. **Nested components**: Moderation reasons cũng sử dụng index làm key có thể gây conflict

## Giải pháp đã thực hiện

### 1. Loại bỏ Duplicate Items từ Data

**File:** `frontend/src/pages/Moderator/components/QueueList.jsx`

```javascript
// Remove duplicate items based on id and created_at
const uniqueItems = (data.tasks || []).filter((item, index, self) => {
  const firstIndex = self.findIndex(
    otherItem => otherItem.id === item.id && otherItem.created_at === item.created_at
  );
  return firstIndex === index;
});
```

**Lợi ích:**
- Loại bỏ duplicate items ngay từ source data
- Giảm số lượng items cần render
- Tránh confusion cho người dùng

### 2. Tạo Unique Keys cho Items

**Trước:**
```javascript
filteredItems.map(item => (
  <div key={item.id}>
```

**Sau:**
```javascript
filteredItems.map((item, index) => (
  <div key={`${item.id}_${item.created_at}_${index}`}>
```

**Lợi ích:**
- Kết hợp ID, timestamp và index để tạo unique key
- Đảm bảo mỗi item có key riêng biệt
- Tránh React reconciliation errors

### 3. Tạo Unique Keys cho Moderation Reasons

**Trước:**
```javascript
{getModerationReasons(item).map((reason, index) => (
  <span key={index}>
```

**Sau:**
```javascript
{getModerationReasons(item).map((reason, reasonIndex) => (
  <span key={`${item.id}_reason_${reasonIndex}_${reason.text}`}>
```

**Lợi ích:**
- Kết hợp item ID, reason index và reason text
- Đảm bảo mỗi reason tag có key unique
- Tránh conflict khi có nhiều items với cùng reasons

## Kết quả

1. **Loại bỏ React warnings**: Không còn duplicate keys warnings
2. **Performance tốt hơn**: Ít items cần render hơn
3. **UX cải thiện**: Không còn duplicate items hiển thị
4. **Stable rendering**: React có thể track components chính xác

## Testing

Để test fix này:

1. Mở Developer Tools
2. Kiểm tra Console tab
3. Navigate đến Moderator Dashboard
4. Xác nhận không còn duplicate keys warnings
5. Kiểm tra danh sách items không có duplicates

## Prevention

Để tránh lỗi này trong tương lai:

1. **API level**: Đảm bảo API không trả về duplicate data
2. **Frontend level**: Luôn sử dụng unique keys cho list items
3. **Code review**: Kiểm tra keys trong tất cả map functions
4. **Testing**: Thêm tests để detect duplicate keys
