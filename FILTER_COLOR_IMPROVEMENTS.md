# Cải thiện màu chữ cho bộ lọc

## Tổng quan

Đã cải thiện màu chữ cho toàn bộ bộ lọc trong trang kiểm duyệt nội dung và danh sách báo cáo để dễ nhìn và phân biệt hơn.

## Những thay đổi đã thực hiện

### 1. ContentModerationDashboard.jsx

#### A. Thêm labels cho các trường lọc

- Thêm label "Mức độ ưu tiên" cho select priority
- Thêm label "Ngôn ngữ" cho select language
- Thêm label "Từ ngày" cho input date_from
- Thêm label "Đến ngày" cho input date_to

#### B. Cập nhật màu chữ

- **Tiêu đề bộ lọc**: Đổi từ `text-gray-900` thành `text-blue-900`
- **Labels**: Sử dụng `text-blue-700` cho tất cả labels
- **Options trong select priority**:
  - "Tất cả ưu tiên": `text-gray-900`
  - "Ưu tiên cao": `text-red-700`
  - "Ưu tiên trung bình": `text-orange-700`
  - "Ưu tiên thấp": `text-green-700`
- **Options trong select language**:
  - "Tất cả ngôn ngữ": `text-gray-900`
  - "Tiếng Việt": `text-blue-700`
  - "Tiếng Anh": `text-purple-700`
- **Input fields**: Thêm `text-gray-900 bg-white` để đảm bảo chữ rõ ràng

### 2. ReportsList.jsx

#### A. Thêm labels cho các trường lọc

- Thêm label "Tìm kiếm" cho input search
- Thêm label "Lý do" cho select reason
- Thêm label "Ưu tiên" cho select priority
- Thêm label "Trạng thái" cho select status

#### B. Cập nhật màu chữ

- **Search icon**: Đổi từ `text-gray-400` thành `text-blue-400`
- **Labels**: Sử dụng `text-blue-700` cho tất cả labels
- **Options trong select reason**:
  - "Tất cả lý do": `text-gray-900`
  - "Ngôn ngữ xúc phạm": `text-red-700`
  - "Lạm dụng": `text-red-700`
  - "Spam": `text-yellow-700`
  - "Spoiler": `text-purple-700`
  - "Không liên quan": `text-blue-700`
- **Options trong select priority**:
  - "Tất cả ưu tiên": `text-gray-900`
  - "Cao": `text-red-700`
  - "Trung bình": `text-orange-700`
  - "Thấp": `text-green-700`
- **Options trong select status**:
  - "Tất cả trạng thái": `text-gray-900`
  - "Chờ xử lý": `text-yellow-700`
  - "Đã xử lý": `text-green-700`
- **Input fields**: Thêm `text-gray-900 bg-white` để đảm bảo chữ rõ ràng

## Lợi ích

1. **Dễ nhìn hơn**: Màu chữ rõ ràng và có độ tương phản tốt
2. **Phân biệt dễ dàng**: Mỗi loại option có màu riêng để dễ nhận biết
3. **UX tốt hơn**: Labels giúp người dùng hiểu rõ chức năng của từng trường
4. **Nhất quán**: Sử dụng cùng một bảng màu cho cả hai trang

## Màu sắc được sử dụng

- **Xanh dương**: Labels, tiêu đề, tùy chọn mặc định
- **Đỏ**: Ưu tiên cao, lý do nghiêm trọng
- **Cam**: Ưu tiên trung bình
- **Vàng**: Spam, chờ xử lý
- **Xanh lá**: Ưu tiên thấp, đã xử lý
- **Tím**: Tiếng Anh, Spoiler
- **Xám**: Tùy chọn "Tất cả"
