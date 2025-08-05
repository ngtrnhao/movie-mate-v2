# Moderator Dashboard API Optimization

## 🔍 Vấn đề đã phát hiện

### Nguyên nhân gây duplicate API calls:

1. **Multiple functions gọi cùng endpoint**:

   - `getDashboardOverview()`
   - `getRecentModerationActivities()`
   - `getModerationPerformanceMetrics()`
   - Tất cả đều gọi `/api/admin/movies/dashboard_overview_data/`

2. **DashboardOverview component gọi 3 API riêng biệt**:

   ```javascript
   const [overviewResponse, activitiesResponse, metricsResponse] = await Promise.all([
     getDashboardOverview(),
     getRecentModerationActivities(5),
     getModerationPerformanceMetrics(),
   ]);
   ```

3. **Component render nhiều lần**:
   - Moderator Dashboard render DashboardOverview ở 2 nơi
   - Có thể do re-render không cần thiết

## ✅ Giải pháp đã áp dụng

### 1. Tối ưu hóa API Service (`moderatorService.js`)

- **Deprecated các function riêng biệt**:

  ```javascript
  // DEPRECATED - Use getDashboardOverview instead
  export const getRecentModerationActivities = async (limit = 10) => {
    console.warn(
      '⚠️ getRecentModerationActivities is deprecated. Use getDashboardOverview instead.'
    );
    const response = await getDashboardOverview();
    return { data: response?.data?.recent_activities || [] };
  };
  ```

- **Single source of truth**: Chỉ `getDashboardOverview()` gọi API thực tế

### 2. Tối ưu hóa DashboardOverview Component

- **Single API call thay vì 3 calls**:

  ```javascript
  // Before: 3 separate API calls
  const [overviewResponse, activitiesResponse, metricsResponse] = await Promise.all([...]);

  // After: Single API call
  const response = await moderationCacheService.cachedApiCall(
    'dashboard_overview_optimized',
    async () => await getDashboardOverview(),
    {}
  );
  ```

- **Extract data từ single response**:
  ```javascript
  const dashboardData = response.data || {};
  setStats(dashboardData.stats || []);
  setRecentActivities(dashboardData.recent_activities || []);
  setPerformanceMetrics(dashboardData.performance_metrics || null);
  ```

### 3. Cải thiện Cache Service

- **Extended TTL cho dashboard data**:

  ```javascript
  dashboard_overview_optimized: 60000, // 60s - Dashboard data can be cached longer
  ```

- **Better cache key recognition**:
  ```javascript
  if (endpoint.includes('dashboard_overview_optimized')) return 'dashboard_overview_optimized';
  ```

### 4. Tối ưu hóa Moderator Dashboard

- **Prevent duplicate renders**: Đảm bảo DashboardOverview chỉ render một lần
- **Better component lifecycle management**

## 📊 Kết quả mong đợi

### Trước khi tối ưu:

- **6 API calls** đến `/api/admin/movies/dashboard_overview_data/`
- **3 API calls** đến `/api/admin/movies/dashboard_statistics/`
- **3 API calls** đến `/api/admin/movies/navigation_badge_counts/`
- **Tổng: 12 API calls** khi load dashboard

### Sau khi tối ưu:

- **1 API call** đến `/api/admin/movies/dashboard_overview_data/` (cached 60s)
- **1 API call** đến `/api/admin/movies/dashboard_statistics/` (cached 30s)
- **1 API call** đến `/api/admin/movies/navigation_badge_counts/` (cached 30s)
- **Tổng: 3 API calls** khi load dashboard

### Lợi ích:

- **Giảm 75% số lượng API calls**
- **Cải thiện performance** đáng kể
- **Giảm tải cho server**
- **Better user experience** với loading nhanh hơn

## 🔧 Cách kiểm tra

### 1. Mở Developer Tools

- F12 → Network tab
- Filter by "dashboard"

### 2. Refresh Moderator Dashboard

- Đếm số lượng calls đến các endpoint
- Kiểm tra cache headers

### 3. Monitor Console

- Xem log messages từ cache service
- Kiểm tra warning messages từ deprecated functions

## 🚨 Lưu ý quan trọng

### Backend API Response Format

Đảm bảo backend trả về đúng format:

```json
{
  "data": {
    "stats": [...],
    "recent_activities": [...],
    "performance_metrics": {...}
  }
}
```

### Migration Path

- Các component khác vẫn có thể sử dụng deprecated functions
- Functions sẽ log warning nhưng vẫn hoạt động
- Dần dần migrate sang `getDashboardOverview()`

### Cache Invalidation

- Cache tự động invalidate sau 60s cho dashboard data
- Có thể manually clear cache nếu cần
- Debug mode có thể enable để monitor cache hits/misses
