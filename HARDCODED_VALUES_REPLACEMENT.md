# Hard-coded Values Replacement Documentation

## Tổng quan

Đã thay thế các hard-coded values trong Moderator Dashboard bằng API calls để hiển thị số liệu thực tế từ database.

## Thay đổi đã thực hiện

### 1. Backend API Endpoint

**File:** `backend/apps/movies/views.py`

**Thêm endpoint:** `moderation_stats`

- **URL:** `/api/movies/reviews/moderation_stats/`
- **Method:** GET
- **Permission:** Moderator/Admin only

**Response format:**

```json
{
  "status": "success",
  "data": {
    "pending": 328,
    "in_progress": 0,
    "completed": 10,
    "today_completed": 5,
    "yesterday_completed": 3,
    "change_percentage": 66.7,
    "reported": 1,
    "spoiler": 226,
    "avg_processing_time": 2.5,
    "total_reviews": 5000
  }
}
```

**Logic tính toán:**

- `pending`: Reviews chưa được duyệt (`is_approved = null`)
- `in_progress`: Reviews có `moderated_by` nhưng chưa `is_approved`
- `completed`: Reviews đã được duyệt (`is_approved = True/False`)
- `today_completed`: Reviews hoàn thành hôm nay
- `reported`: Số reviews bị báo cáo
- `spoiler`: Số reviews được đánh dấu spoiler
- `avg_processing_time`: Thời gian xử lý trung bình (giờ)

### 2. Frontend API Function

**File:** `frontend/src/api/movieService.js`

**Thêm function:** `getModerationStats()`

```javascript
export const getModerationStats = async () => {
  try {
    const response = await axiosInstance.get(
      "/api/movies/reviews/moderation_stats/"
    );
    return response.data;
  } catch (error) {
    console.error("Error fetching moderation stats:", error);
    throw error;
  }
};
```

### 3. Dashboard Component Update

**File:** `frontend/src/pages/Moderator/Dashboard.jsx`

**Thay đổi chính:**

#### A. Thêm state cho stats

```javascript
const [dashboardStats, setDashboardStats] = useState([]);
const [moderationStats, setModerationStats] = useState({
  pending: 0,
  in_progress: 0,
  completed: 0,
  today_completed: 0,
  reported: 0,
  spoiler: 0,
  avg_processing_time: 0,
});
```

#### B. Fetch stats on component mount

```javascript
useEffect(() => {
  const fetchStats = async () => {
    try {
      const response = await getModerationStats();
      if (response.status === "success") {
        setModerationStats(response.data);
        // Update dashboard stats with real data
        const stats = [
          {
            title: "Nội dung chờ duyệt",
            value: response.data.pending.toString(),
            change:
              response.data.pending > 0 ? `+${response.data.pending}` : "0",
            // ... other properties
          },
          // ... other stats
        ];
        setDashboardStats(stats);
      }
    } catch (error) {
      console.error("Failed to fetch moderation stats:", error);
      // Fallback to default stats
    }
  };

  fetchStats();
}, []);
```

#### C. Thay thế hard-coded values

**Trước:**

```javascript
<p className="text-2xl font-bold text-gray-900">23</p>  // Hard-coded
<p className="text-2xl font-bold text-gray-900">8</p>   // Hard-coded
<p className="text-2xl font-bold text-gray-900">156</p> // Hard-coded
```

**Sau:**

```javascript
<p className="text-2xl font-bold text-gray-900">{moderationStats.pending}</p>
<p className="text-2xl font-bold text-gray-900">{moderationStats.in_progress}</p>
<p className="text-2xl font-bold text-gray-900">{moderationStats.completed}</p>
```

## Lợi ích

### 1. **Dữ liệu thực tế**

- Hiển thị số liệu chính xác từ database
- Không còn hard-coded values sai lệch

### 2. **Real-time updates**

- Stats được cập nhật mỗi khi component mount
- Phản ánh trạng thái hiện tại của hệ thống

### 3. **Tính nhất quán**

- Logic đếm thống nhất giữa backend và frontend
- Dựa trên các trường dữ liệu thực tế

### 4. **Dễ bảo trì**

- Không cần sửa code khi thay đổi logic đếm
- Tập trung logic ở backend

## Testing

### 1. Test API endpoint

```bash
python test_moderation_stats_api.py
```

### 2. Kiểm tra frontend

- Mở Moderator Dashboard
- Xem stats có hiển thị số liệu thực tế
- Refresh page để kiểm tra API call

### 3. Validation

- `pending + in_progress` = tổng reviews chưa hoàn thành
- `completed >= today_completed`
- Tất cả số liệu >= 0

## Troubleshooting

### 1. API không trả về dữ liệu

- Kiểm tra authentication token
- Kiểm tra user có quyền Moderator/Admin
- Kiểm tra database có dữ liệu

### 2. Frontend hiển thị 0

- Kiểm tra network tab trong browser
- Kiểm tra console errors
- Kiểm tra API response format

### 3. Stats không cập nhật

- Kiểm tra useEffect dependency
- Kiểm tra API call có thành công
- Kiểm tra state update logic

## Kết luận

Việc thay thế hard-coded values bằng API calls đã:

- ✅ Cải thiện độ chính xác của dữ liệu
- ✅ Tăng tính real-time của dashboard
- ✅ Dễ dàng bảo trì và mở rộng
- ✅ Đảm bảo tính nhất quán dữ liệu

Dashboard giờ đây hiển thị số liệu thực tế từ database thay vì các giá trị cố định.
