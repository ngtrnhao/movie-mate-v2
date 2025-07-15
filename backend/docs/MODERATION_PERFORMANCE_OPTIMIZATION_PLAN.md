# 🚀 Moderation Performance Optimization Plan

## 📊 **Vấn đề đã phát hiện**

### 1. **Performance Issues**

- **API Response Time**: 4 phút cho mỗi API call
- **Duplicate Calls**: `moderation_queue` và `spoiler_statistics` được gọi duplicate
- **N+1 Query Problem**: Backend process từng review một cách không hiệu quả

### 2. **Root Causes**

#### **Backend Issues:**

- **`moderation_queue` API**:

  - Load tất cả reviews chưa được moderate
  - Chạy spoiler detection AI cho TỪNG review
  - Multiple database queries cho mỗi review (`reports.count()`, `reports.values_list()`)
  - Không có pagination ở database level

- **`spoiler_statistics` API**:
  - Load tất cả reviews của user/system
  - Chạy spoiler detection cho từng review
  - Không có time limit

#### **Frontend Issues:**

- **Duplicate useEffect**: Gọi cả 2 APIs mỗi khi `filters` hoặc `page` thay đổi
- **Unnecessary Refreshes**: Refresh cả 2 APIs sau mỗi moderation action

---

## ✅ **Giải pháp đã implement**

### **Phase 1: Backend Optimizations**

#### **1.1 Optimized Moderation Queue API**

📁 `backend/apps/movies/views.py` - `moderation_queue_optimized()`

**Improvements:**

- ✅ **Database-level aggregations**: `Count()`, `Exists()`, `OuterRef()`
- ✅ **Pre-filtering**: Chỉ load reviews cần moderation
- ✅ **Selective spoiler detection**: Chỉ chạy cho uncertain cases
- ✅ **Proper pagination**: Database-level với `[start:end]`
- ✅ **Cached thresholds**: Tránh repeated calls
- ✅ **Performance metrics**: Track số lượng spoiler detections

**Performance Gains:**

```python
# Before: Load ALL reviews → Process ALL → Filter → Paginate
# After:  Filter at DB → Paginate at DB → Process ONLY paginated results
```

#### **1.2 Optimized Spoiler Statistics API**

📁 `backend/apps/movies/views.py` - `spoiler_statistics_optimized()`

**Improvements:**

- ✅ **Time-limited analysis**: Default 30 days (max 90 days)
- ✅ **Database aggregations**: `Count()`, `Q()` filters
- ✅ **Sample-based analysis**: Chỉ analyze 100 latest spoiler reviews
- ✅ **Efficient language detection**: Built-in logic
- ✅ **Cached calculations**: Pre-computed stats

**Performance Gains:**

```python
# Before: Process ALL reviews ever created
# After:  Process ONLY recent reviews (30-90 days) + sample analysis
```

### **Phase 2: URL Configuration**

📁 `backend/apps/movies/urls.py`

**New Endpoints:**

```python
# Optimized endpoints
path('reviews/moderation_queue_optimized/', ...)
path('reviews/spoiler_statistics_optimized/', ...)

# Original endpoints (kept for backward compatibility)
path('reviews/moderation_queue/', ...)
path('reviews/spoiler_statistics/', ...)
```

### **Phase 3: Frontend Optimizations**

#### **3.1 API Service Updates**

📁 `frontend/src/api/movieService.js`

**New Functions:**

- ✅ `getModerationQueueOptimized()` - Uses optimized endpoint
- ✅ `getSpoilerStatisticsOptimized(days)` - With time limit parameter
- ✅ **Fallback mechanism**: Auto-fallback to original APIs if optimized fails

#### **3.2 Component Optimizations**

📁 `frontend/src/pages/Moderator/components/ContentModerationDashboard.jsx`

**Improvements:**

- ✅ **Separated useEffect hooks**: Tránh unnecessary calls
- ✅ **Smart refresh strategy**:
  - `moderation_queue`: Refresh after every action
  - `spoiler_statistics`: Refresh occasionally (30% chance for single actions, 50% for bulk)
- ✅ **Performance logging**: Console logs để monitor performance
- ✅ **Error handling**: Graceful fallback to original APIs

**Before:**

```javascript
useEffect(() => {
  fetchModerationQueue(); // 4 phút
  fetchSpoilerStats(); // 4 phút
}, [currentPage, filters]); // Duplicate calls on every change
```

**After:**

```javascript
// Separate effects
useEffect(() => {
  fetchModerationQueue(); // < 30 giây
}, [currentPage, filters]);

useEffect(() => {
  fetchSpoilerStats(); // < 10 giây (30-day limit)
}, []); // Only on mount
```

---

## 📈 **Expected Performance Improvements**

### **API Response Times:**

- **`moderation_queue_optimized`**: `4 phút → 15-30 giây` (80-90% improvement)
- **`spoiler_statistics_optimized`**: `4 phút → 5-10 giây` (95% improvement)

### **Database Queries:**

- **Before**: N+1 queries (1 + N\*3 queries per review)
- **After**: 2-3 queries total với aggregations

### **Spoiler Detection Calls:**

- **Before**: Run for ALL reviews (có thể hàng nghìn)
- **After**: Run for ONLY paginated uncertain cases (max 20-50 per request)

### **Frontend Network Calls:**

- **Before**: Duplicate calls on every filter change
- **After**: Smart refresh strategy, 50-70% reduction in calls

---

## 🔧 **Implementation Status**

### ✅ **Completed:**

1. Backend optimized APIs
2. URL routing for new endpoints
3. Frontend API service functions
4. Component optimization with smart refresh
5. Error handling and fallback mechanisms
6. Performance logging

### 🔄 **Next Steps (Recommendations):**

#### **Phase 4: Database Indexes** (Tuần tới)

```sql
-- Add indexes for performance
CREATE INDEX idx_moviereview_moderation_lookup
ON movies_moviereview(review_type, is_public, is_approved, created_at);

CREATE INDEX idx_moviereview_spoiler_lookup
ON movies_moviereview(is_spoiler, created_at, language);
```

#### **Phase 5: Caching Layer** (2 tuần tới)

- Redis caching for spoiler statistics (30-minute cache)
- Database query result caching
- API response caching

#### **Phase 6: Background Processing** (1 tháng tới)

- Celery tasks cho spoiler analysis
- Pre-computed moderation scores
- Scheduled statistics updates

---

## 🧪 **Testing Instructions**

### **1. Test Optimized APIs:**

```bash
# Test optimized moderation queue
curl "http://localhost:8000/api/reviews/moderation_queue_optimized/?page=1&page_size=20"

# Test optimized spoiler statistics
curl "http://localhost:8000/api/reviews/spoiler_statistics_optimized/?days=30"
```

### **2. Monitor Performance:**

- Check browser DevTools Network tab
- Look for console performance logs
- Monitor database query logs

### **3. Fallback Testing:**

- Temporarily break optimized endpoint
- Verify fallback to original APIs works

---

## 📊 **Performance Monitoring**

### **Console Logs to Watch:**

```javascript
✅ Optimized moderation queue loaded: { count: 20, performance: {...} }
✅ Optimized spoiler stats loaded: { analyzed: 100, performance: {...} }
⚠️ Falling back to original API...
```

### **Network Tab Monitoring:**

- **Before**: 2 requests taking 8+ phút total
- **After**: 2 requests taking 30-40 giây total

---

## 🎯 **Success Metrics**

- [ ] **API Response Time**: < 30 giây cho moderation_queue
- [ ] **API Response Time**: < 10 giây cho spoiler_statistics
- [ ] **Reduced Network Calls**: 50-70% reduction
- [ ] **User Experience**: No loading timeout issues
- [ ] **Fallback Success**: 100% availability với fallback

---

## 🔗 **Related Files Modified**

1. `backend/apps/movies/views.py` - Optimized API implementations
2. `backend/apps/movies/urls.py` - New endpoint routing
3. `frontend/src/api/movieService.js` - Optimized API functions
4. `frontend/src/pages/Moderator/components/ContentModerationDashboard.jsx` - Smart refresh logic

---

_Tài liệu này sẽ được cập nhật theo progress của optimization efforts._
