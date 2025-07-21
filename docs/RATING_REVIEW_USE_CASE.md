# **Biểu Đồ Use Case - Chức Năng Rating & Review**

## **Mô Tả Tổng Quan**

Biểu đồ use case này mô tả các chức năng liên quan đến việc đánh giá (rating) và viết review phim trong hệ thống Movie Recommendation. Hệ thống hỗ trợ cả rating đơn giản và review chi tiết với các tính năng bảo mật, kiểm duyệt và tương tác người dùng.

---

## **PHẦN 1: RATING & REVIEW CHO NGƯỜI DÙNG**

### **Biểu Đồ Use Case - Người Dùng**

```mermaid
graph TB
    subgraph "Actors"
        U[👤 Người dùng đã đăng ký]
        S[🔒 Hệ thống Bảo mật]
        N[🤖 Hệ thống Thông báo]
        C[💾 Hệ thống Cache]
    end

    subgraph "Primary Use Cases"
        UC1[Đánh giá phim]
        UC2[Viết Review phim]
        UC3[Xem danh sách Reviews]
        UC4[Chỉnh sửa Review]
        UC5[Xóa Review]
        UC6[Đánh giá hữu ích]
        UC7[Báo cáo Review]
    end

    subgraph "Supporting Use Cases"
        UC8[Validate dữ liệu Rating]
        UC9[Validate nội dung Review]
        UC10[Kiểm tra quyền truy cập]
        UC11[Kiểm tra giới hạn Review]
        UC12[Phát hiện Spoiler]
        UC13[Ghi log hoạt động]
        UC14[Cập nhật thống kê]
        UC15[Gửi thông báo]
        UC16[Cache dữ liệu]
        UC17[Xử lý lỗi]
        UC18[Tính toán điểm hữu ích]
        UC19[Kiểm tra trùng lặp]
    end

    %% Actor connections
    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    U --> UC7

    S --> UC8
    S --> UC9
    S --> UC10
    S --> UC12
    S --> UC13

    N --> UC15
    C --> UC16

    %% Include relationships
    UC1 -->|<<include>> UC8
    UC1 -->|<<include>> UC10
    UC1 -->|<<include>> UC13
    UC1 -->|<<include>> UC14
    UC1 -->|<<include>> UC16
    UC1 -->|<<include>> UC19

    UC2 -->|<<include>> UC9
    UC2 -->|<<include>> UC10
    UC2 -->|<<include>> UC11
    UC2 -->|<<include>> UC12
    UC2 -->|<<include>> UC13
    UC2 -->|<<include>> UC14
    UC2 -->|<<include>> UC15
    UC2 -->|<<include>> UC16
    UC2 -->|<<include>> UC19

    UC3 -->|<<include>> UC10
    UC3 -->|<<include>> UC16
    UC3 -->|<<include>> UC18

    UC4 -->|<<include>> UC9
    UC4 -->|<<include>> UC10
    UC4 -->|<<include>> UC12
    UC4 -->|<<include>> UC13
    UC4 -->|<<include>> UC14
    UC4 -->|<<include>> UC15

    UC5 -->|<<include>> UC10
    UC5 -->|<<include>> UC13
    UC5 -->|<<include>> UC14
    UC5 -->|<<include>> UC15

    UC6 -->|<<include>> UC10
    UC6 -->|<<include>> UC13
    UC6 -->|<<include>> UC18

    UC7 -->|<<include>> UC10
    UC7 -->|<<include>> UC13
    UC7 -->|<<include>> UC15

    UC8 -->|<<include>> UC17
    UC9 -->|<<include>> UC17
    UC12 -->|<<include>> UC17
```

### **Mô Tả Chi Tiết - Phần Người Dùng**

#### **Primary Use Cases**

##### **UC1: Đánh giá phim**

- **Mô tả**: Người dùng đánh giá phim bằng số sao (0.0-5.0)
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Validate dữ liệu, Kiểm tra quyền, Ghi log, Cập nhật thống kê, Cache dữ liệu, Kiểm tra trùng lặp
- **Điều kiện**: Người dùng đã đăng nhập, phim tồn tại
- **Kết quả**: Rating được lưu vào database, thống kê được cập nhật

##### **UC2: Viết Review phim**

- **Mô tả**: Người dùng viết review chi tiết cho phim
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Validate nội dung, Kiểm tra quyền, Kiểm tra giới hạn, Phát hiện spoiler, Ghi log, Cập nhật thống kê, Gửi thông báo, Cache dữ liệu, Kiểm tra trùng lặp
- **Điều kiện**: Người dùng đã đăng nhập, chưa vượt quá giới hạn review
- **Kết quả**: Review được tạo, có thể cần kiểm duyệt

##### **UC3: Xem danh sách Reviews**

- **Mô tả**: Người dùng xem danh sách reviews của phim
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Kiểm tra quyền, Cache dữ liệu, Tính toán điểm hữu ích
- **Điều kiện**: Phim tồn tại
- **Kết quả**: Hiển thị danh sách reviews đã được kiểm duyệt

##### **UC4: Chỉnh sửa Review**

- **Mô tả**: Người dùng chỉnh sửa review đã viết
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Validate nội dung, Kiểm tra quyền, Phát hiện spoiler, Ghi log, Cập nhật thống kê, Gửi thông báo
- **Điều kiện**: Review thuộc về người dùng, chưa bị khóa
- **Kết quả**: Review được cập nhật, có thể cần kiểm duyệt lại

##### **UC5: Xóa Review**

- **Mô tả**: Người dùng xóa review của mình
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Kiểm tra quyền, Ghi log, Cập nhật thống kê, Gửi thông báo
- **Điều kiện**: Review thuộc về người dùng
- **Kết quả**: Review bị xóa, thống kê được cập nhật

##### **UC6: Đánh giá hữu ích**

- **Mô tả**: Người dùng đánh giá review có hữu ích hay không
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Kiểm tra quyền, Ghi log, Tính toán điểm hữu ích
- **Kết quả**: Cập nhật điểm hữu ích của review

##### **UC7: Báo cáo Review**

- **Mô tả**: Người dùng báo cáo review vi phạm
- **Actor chính**: Người dùng đã đăng ký
- **Include**: Kiểm tra quyền, Ghi log, Gửi thông báo
- **Kết quả**: Báo cáo được gửi cho moderator

#### **Supporting Use Cases**

##### **UC8: Validate dữ liệu Rating**

- **Mô tả**: Kiểm tra tính hợp lệ của rating
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: Rating phải từ 0.0 đến 5.0
- **Kết quả**: Rating hợp lệ hoặc báo lỗi

##### **UC9: Validate nội dung Review**

- **Mô tả**: Kiểm tra nội dung review
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: Nội dung tối thiểu 10 ký tự, không chứa nội dung cấm
- **Kết quả**: Nội dung hợp lệ hoặc báo lỗi

##### **UC10: Kiểm tra quyền truy cập**

- **Mô tả**: Xác thực quyền của người dùng
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: JWT token hợp lệ
- **Kết quả**: Cho phép hoặc từ chối truy cập

##### **UC11: Kiểm tra giới hạn Review**

- **Mô tả**: Kiểm tra số lượng review của người dùng
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: Chưa vượt quá giới hạn theo gói subscription
- **Kết quả**: Cho phép hoặc từ chối tạo review

##### **UC12: Phát hiện Spoiler**

- **Mô tả**: Tự động phát hiện nội dung spoiler
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: Sử dụng AI/ML để phân tích nội dung
- **Kết quả**: Đánh dấu review có spoiler

##### **UC13: Ghi log hoạt động**

- **Mô tả**: Ghi lại tất cả hoạt động liên quan
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Log được lưu vào database

##### **UC14: Cập nhật thống kê**

- **Mô tả**: Cập nhật thống kê phim và người dùng
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Thống kê được cập nhật real-time

##### **UC15: Gửi thông báo**

- **Mô tả**: Gửi thông báo cho người dùng liên quan
- **Actor**: Hệ thống Thông báo
- **Kết quả**: Email/notification được gửi

##### **UC16: Cache dữ liệu**

- **Mô tả**: Cache dữ liệu để tăng hiệu suất
- **Actor**: Hệ thống Cache
- **Kết quả**: Dữ liệu được cache

##### **UC17: Xử lý lỗi**

- **Mô tả**: Xử lý các lỗi phát sinh
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Lỗi được xử lý và thông báo

##### **UC18: Tính toán điểm hữu ích**

- **Mô tả**: Tính toán tỷ lệ hữu ích của review dựa trên votes
- **Actor**: Hệ thống Bảo mật
- **Công thức**: `helpfulness_ratio = (helpful_votes / total_votes) * 100`
- **Điều kiện**: Có ít nhất 1 vote
- **Kết quả**: Tỷ lệ hữu ích được tính và cập nhật (0-100%)
- **Ví dụ**: 8 helpful votes / 10 total votes = 80% hữu ích
- **Implementation**: Sử dụng method `get_helpfulness_ratio()` trong MovieReview model

##### **UC19: Kiểm tra trùng lặp**

- **Mô tả**: Kiểm tra review trùng lặp
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Ngăn chặn review trùng lặp

---

## **PHẦN 2: QUẢN TRỊ VÀ KIỂM DUYỆT**

### **Biểu Đồ Use Case - Quản Trị**

```mermaid
graph TB
    subgraph "Actors"
        A[👨‍💼 Admin]
        M[👮‍♂️ Moderator]
        S[🔒 Hệ thống Bảo mật]
        N[🤖 Hệ thống Thông báo]
        AI[🤖 Hệ thống AI]
    end

    subgraph "Primary Use Cases"
        UC20[Xem danh sách Reviews chờ kiểm duyệt]
        UC21[Kiểm duyệt Review]
        UC22[Xem báo cáo vi phạm]
        UC23[Xử lý báo cáo]
        UC24[Quản lý từ khóa cấm]
        UC25[Xem thống kê kiểm duyệt]
        UC26[Khóa/Mở khóa Review]
        UC27[Khóa/Mở khóa User]
    end

    subgraph "Supporting Use Cases"
        UC28[Kiểm tra quyền Admin]
        UC29[Phân tích nội dung AI]
        UC30[Ghi log hoạt động]
        UC31[Cập nhật trạng thái Review]
        UC32[Gửi thông báo cho User]
        UC33[Cập nhật thống kê]
        UC34[Xử lý lỗi]
        UC35[Tạo báo cáo kiểm duyệt]
        UC36[Quản lý blacklist]
        UC37[Phân tích xu hướng vi phạm]
    end

    %% Actor connections
    A --> UC20
    A --> UC21
    A --> UC22
    A --> UC23
    A --> UC24
    A --> UC25
    A --> UC26
    A --> UC27

    M --> UC20
    M --> UC21
    M --> UC22
    M --> UC23
    M --> UC26

    S --> UC28
    S --> UC30
    S --> UC31
    S --> UC33

    N --> UC32
    AI --> UC29
    AI --> UC37

    %% Include relationships
    UC20 -->|<<include>> UC28
    UC20 -->|<<include>> UC30
    UC20 -->|<<include>> UC29

    UC21 -->|<<include>> UC28
    UC21 -->|<<include>> UC29
    UC21 -->|<<include>> UC30
    UC21 -->|<<include>> UC31
    UC21 -->|<<include>> UC32
    UC21 -->|<<include>> UC33

    UC22 -->|<<include>> UC28
    UC22 -->|<<include>> UC30
    UC22 -->|<<include>> UC37

    UC23 -->|<<include>> UC28
    UC23 -->|<<include>> UC30
    UC23 -->|<<include>> UC31
    UC23 -->|<<include>> UC32
    UC23 -->|<<include>> UC33

    UC24 -->|<<include>> UC28
    UC24 -->|<<include>> UC30
    UC24 -->|<<include>> UC36

    UC25 -->|<<include>> UC28
    UC25 -->|<<include>> UC30
    UC25 -->|<<include>> UC35
    UC25 -->|<<include>> UC37

    UC26 -->|<<include>> UC28
    UC26 -->|<<include>> UC30
    UC26 -->|<<include>> UC31
    UC26 -->|<<include>> UC32
    UC26 -->|<<include>> UC33

    UC27 -->|<<include>> UC28
    UC27 -->|<<include>> UC30
    UC27 -->|<<include>> UC31
    UC27 -->|<<include>> UC32
    UC27 -->|<<include>> UC33

    UC29 -->|<<include>> UC34
    UC35 -->|<<include>> UC34
    UC37 -->|<<include>> UC34
```

### **Mô Tả Chi Tiết - Phần Quản Trị**

#### **Primary Use Cases**

##### **UC20: Xem danh sách Reviews chờ kiểm duyệt**

- **Mô tả**: Admin/Moderator xem danh sách reviews cần kiểm duyệt
- **Actor chính**: Admin, Moderator
- **Include**: Kiểm tra quyền Admin, Ghi log hoạt động, Phân tích nội dung AI
- **Điều kiện**: Có quyền admin/moderator
- **Kết quả**: Hiển thị danh sách reviews chờ xử lý

##### **UC21: Kiểm duyệt Review**

- **Mô tả**: Admin/Moderator phê duyệt hoặc từ chối review
- **Actor chính**: Admin, Moderator
- **Include**: Kiểm tra quyền Admin, Phân tích nội dung AI, Ghi log, Cập nhật trạng thái, Gửi thông báo, Cập nhật thống kê
- **Điều kiện**: Review đang chờ kiểm duyệt
- **Kết quả**: Review được phê duyệt/từ chối, thông báo cho user

##### **UC22: Xem báo cáo vi phạm**

- **Mô tả**: Admin/Moderator xem danh sách báo cáo vi phạm
- **Actor chính**: Admin, Moderator
- **Include**: Kiểm tra quyền Admin, Ghi log hoạt động, Phân tích xu hướng vi phạm
- **Điều kiện**: Có quyền admin/moderator
- **Kết quả**: Hiển thị danh sách báo cáo

##### **UC23: Xử lý báo cáo**

- **Mô tả**: Admin/Moderator xử lý báo cáo vi phạm
- **Actor chính**: Admin, Moderator
- **Include**: Kiểm tra quyền Admin, Ghi log, Cập nhật trạng thái, Gửi thông báo, Cập nhật thống kê
- **Điều kiện**: Báo cáo hợp lệ
- **Kết quả**: Báo cáo được xử lý, thông báo cho user

##### **UC24: Quản lý từ khóa cấm**

- **Mô tả**: Admin quản lý danh sách từ khóa cấm
- **Actor chính**: Admin
- **Include**: Kiểm tra quyền Admin, Ghi log hoạt động, Quản lý blacklist
- **Điều kiện**: Có quyền admin
- **Kết quả**: Blacklist được cập nhật

##### **UC25: Xem thống kê kiểm duyệt**

- **Mô tả**: Admin xem thống kê hoạt động kiểm duyệt
- **Actor chính**: Admin
- **Include**: Kiểm tra quyền Admin, Ghi log hoạt động, Tạo báo cáo kiểm duyệt, Phân tích xu hướng vi phạm
- **Điều kiện**: Có quyền admin
- **Kết quả**: Báo cáo thống kê được tạo

##### **UC26: Khóa/Mở khóa Review**

- **Mô tả**: Admin/Moderator khóa hoặc mở khóa review
- **Actor chính**: Admin, Moderator
- **Include**: Kiểm tra quyền Admin, Ghi log, Cập nhật trạng thái, Gửi thông báo, Cập nhật thống kê
- **Điều kiện**: Review tồn tại
- **Kết quả**: Review bị khóa/mở khóa

##### **UC27: Khóa/Mở khóa User**

- **Mô tả**: Admin khóa hoặc mở khóa tài khoản user
- **Actor chính**: Admin
- **Include**: Kiểm tra quyền Admin, Ghi log, Cập nhật trạng thái, Gửi thông báo, Cập nhật thống kê
- **Điều kiện**: User tồn tại
- **Kết quả**: User bị khóa/mở khóa

#### **Supporting Use Cases**

##### **UC28: Kiểm tra quyền Admin**

- **Mô tả**: Xác thực quyền admin/moderator
- **Actor**: Hệ thống Bảo mật
- **Điều kiện**: JWT token hợp lệ, có role admin/moderator
- **Kết quả**: Cho phép hoặc từ chối truy cập

##### **UC29: Phân tích nội dung AI**

- **Mô tả**: Sử dụng AI để phân tích nội dung review
- **Actor**: Hệ thống AI
- **Điều kiện**: Nội dung review cần phân tích
- **Kết quả**: Kết quả phân tích (spam, vi phạm, spoiler)

##### **UC30: Ghi log hoạt động**

- **Mô tả**: Ghi lại tất cả hoạt động quản trị
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Log được lưu vào database

##### **UC31: Cập nhật trạng thái Review**

- **Mô tả**: Cập nhật trạng thái review (approved, rejected, blocked)
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Trạng thái review được cập nhật

##### **UC32: Gửi thông báo cho User**

- **Mô tả**: Gửi thông báo cho user về quyết định kiểm duyệt
- **Actor**: Hệ thống Thông báo
- **Kết quả**: Email/notification được gửi

##### **UC33: Cập nhật thống kê**

- **Mô tả**: Cập nhật thống kê kiểm duyệt
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Thống kê được cập nhật real-time

##### **UC34: Xử lý lỗi**

- **Mô tả**: Xử lý các lỗi phát sinh trong quá trình quản trị
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Lỗi được xử lý và thông báo

##### **UC35: Tạo báo cáo kiểm duyệt**

- **Mô tả**: Tạo báo cáo chi tiết về hoạt động kiểm duyệt
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Báo cáo được tạo

##### **UC36: Quản lý blacklist**

- **Mô tả**: Quản lý danh sách từ khóa và nội dung cấm
- **Actor**: Hệ thống Bảo mật
- **Kết quả**: Blacklist được cập nhật

##### **UC37: Phân tích xu hướng vi phạm**

- **Mô tả**: Phân tích xu hướng vi phạm để cải thiện hệ thống
- **Actor**: Hệ thống AI
- **Kết quả**: Báo cáo xu hướng được tạo

---

## **Các Model Database Liên Quan**

### **MovieReview Model**

```python
class MovieReview(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review_type = models.CharField(max_length=20, default='USER')
    is_spoiler = models.BooleanField(default=False)
    is_approved = models.BooleanField(null=True, blank=True)
    moderated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_reason = models.TextField(blank=True, null=True)
    helpful_votes = models.IntegerField(default=0)
    total_votes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

### **ReviewVote Model**

```python
class ReviewVote(models.Model):
    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
```

### **ReviewReport Model**

```python
class ReviewReport(models.Model):
    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE)
    reported_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    reason = models.CharField(max_length=32, choices=REPORT_REASONS)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## **API Endpoints**

### **Rating & Review APIs (Người dùng)**

- `POST /api/movies/{movie_id}/rate/` - Đánh giá phim
- `POST /api/movies/{movie_id}/review/` - Viết review
- `GET /api/movies/{movie_id}/reviews/` - Xem danh sách reviews
- `PUT /api/reviews/{review_id}/` - Chỉnh sửa review
- `DELETE /api/reviews/{review_id}/` - Xóa review
- `POST /api/reviews/{review_id}/vote/` - Đánh giá hữu ích
- `POST /api/reviews/{review_id}/report/` - Báo cáo review

### **Moderation APIs (Admin/Moderator)**

- `GET /api/admin/reviews/pending/` - Xem reviews chờ kiểm duyệt
- `POST /api/admin/reviews/{review_id}/moderate/` - Kiểm duyệt review
- `GET /api/admin/reports/` - Xem báo cáo vi phạm
- `POST /api/admin/reports/{report_id}/handle/` - Xử lý báo cáo
- `GET /api/admin/moderation/stats/` - Thống kê kiểm duyệt
- `POST /api/admin/reviews/{review_id}/block/` - Khóa review
- `POST /api/admin/users/{user_id}/block/` - Khóa user

## **Tính Năng Đặc Biệt**

### **Spoiler Detection**

- Sử dụng AI/ML để tự động phát hiện nội dung spoiler
- Đánh dấu review có spoiler và cảnh báo người dùng
- Cho phép người dùng chọn xem hoặc ẩn spoiler

### **Review Limits**

- Giới hạn số lượng review theo gói subscription
- Free users: 5 reviews/tháng
- Premium users: 50 reviews/tháng
- Unlimited users: Không giới hạn

### **Moderation System**

- Tự động kiểm duyệt với AI
- Manual review bởi moderator
- Hệ thống báo cáo từ người dùng
- Blacklist từ khóa và nội dung cấm

### **Voting System**

- Người dùng có thể vote "helpful" hoặc "not helpful"
- Tính toán tỷ lệ hữu ích của review
- Sắp xếp reviews theo độ hữu ích

### **Analytics & Statistics**

- Thống kê rating trung bình của phim
- Số lượng reviews, votes
- Trending reviews
- User engagement metrics
- Moderation performance metrics
