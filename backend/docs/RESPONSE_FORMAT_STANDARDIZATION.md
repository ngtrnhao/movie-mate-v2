# Response Format Standardization & Rating Distribution Format

## 📋 Tổng quan

Tài liệu này mô tả các thay đổi đã thực hiện để standardize response format và rating distribution format giữa frontend và backend.

## 🔧 Các thay đổi đã thực hiện

### 1. **Frontend API Standardization**

#### **File: `frontend/src/api/movieService.js`**

**Trước:**

```javascript
export const getMovieReviews = async (
  movieId,
  page = 1,
  limit = 20,
  sortBy = "recent"
) => {
  const response = await axiosInstance.get(`/api/movies/${movieId}/reviews/`, {
    params: { page, page_size: limit, sort_by: sortBy },
  });
  return response.data; // Trả về trực tiếp response.data
};
```

**Sau:**

```javascript
export const getMovieReviews = async (
  movieId,
  page = 1,
  limit = 20,
  sortBy = "recent"
) => {
  const response = await axiosInstance.get(`/api/movies/${movieId}/reviews/`, {
    params: { page, page_size: limit, sort_by: sortBy },
  });

  // Standardize response format
  const responseData = response.data;
  return {
    data: responseData.data || [],
    total_pages: responseData.total_pages || 1,
    current_page: responseData.current_page || page,
    count: responseData.count || 0,
    // Add rating distribution if available
    rating_distribution: responseData.rating_distribution || {},
    average_rating: responseData.average_rating || 0,
    total_ratings: responseData.total_ratings || 0,
  };
};
```

**Trước:**

```javascript
export const getUserReview = async (movieId) => {
  const response = await axiosInstance.get(`/api/reviews/my_reviews/`, {
    params: { movie_id: movieId },
  });
  return response.data;
};
```

**Sau:**

```javascript
export const getUserReview = async (movieId) => {
  const response = await axiosInstance.get(`/api/reviews/my_reviews/`, {
    params: { movie_id: movieId },
  });

  // Standardize response format
  const responseData = response.data;
  return {
    data: responseData.data || [],
    results: responseData.data || [], // Keep backward compatibility
    count: responseData.count || 0,
    status: responseData.status || "success",
  };
};
```

#### **File: `frontend/src/api/profileService.js`**

**Trước:**

```javascript
export const getUserRatings = async (userId, page = 1, language = "vi") => {
  const response = await axiosInstance.get(
    `/api/auth/profile/${userId}/ratings/`,
    {
      params: { page, language },
    }
  );
  return response.data;
};
```

**Sau:**

```javascript
export const getUserRatings = async (userId, page = 1, language = "vi") => {
  const response = await axiosInstance.get(
    `/api/auth/profile/${userId}/ratings/`,
    {
      params: { page, language },
    }
  );

  // Standardize response format
  const responseData = response.data;
  return {
    results: responseData.results || responseData.data || [],
    data: responseData.results || responseData.data || [],
    count: responseData.count || 0,
    next: responseData.next || null,
    previous: responseData.previous || null,
    status: responseData.status || "success",
  };
};
```

### 2. **Frontend Component Updates**

#### **File: `frontend/src/pages/Movies/components/RatingTab.jsx`**

**Trước:**

```javascript
const fetchReviews = async () => {
  const data = await getMovieReviews(movieId, currentPage, 10, sortBy);

  // Calculate stats from reviews
  const distribution = {};
  (data.data || []).forEach((r) => {
    const ratingValue = parseFloat(r.rating) || 0;
    const stars = Math.round(ratingValue);
    if (stars > 0) {
      distribution[stars] = (distribution[stars] || 0) + 1;
    }
  });
};
```

**Sau:**

```javascript
const fetchReviews = async () => {
  const data = await getMovieReviews(movieId, currentPage, 10, sortBy);

  // Use rating distribution from backend if available, otherwise calculate from reviews
  let distribution = {};
  let total = 0;
  let sum = 0;

  if (
    data.rating_distribution &&
    Object.keys(data.rating_distribution).length > 0
  ) {
    // Use backend rating distribution
    distribution = data.rating_distribution;
    total = data.total_ratings || 0;
    sum = (data.average_rating || 0) * total;
  } else {
    // Calculate from reviews (fallback)
    (data.data || []).forEach((r) => {
      const ratingValue = parseFloat(r.rating) || 0;
      const stars = Math.round(ratingValue);
      if (stars > 0) {
        distribution[stars] = (distribution[stars] || 0) + 1;
        total += 1;
        sum += ratingValue;
      }
    });
  }

  setStats({
    averageRating:
      data.average_rating || (total ? (sum / total).toFixed(1) : 0),
    totalRatings: data.total_ratings || total,
    distribution,
  });
};
```

### 3. **Backend API Updates**

#### **File: `backend/apps/movies/views.py`**

**Trước:**

```python
@action(detail=False, methods=['get'])
def stats(self, request):
    stats = {
        'total_reviews': reviews.count(),
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'rating_distribution': reviews.values('rating').annotate(count=Count('id')).order_by('rating'),
        # ...
    }
```

**Sau:**

```python
@action(detail=False, methods=['get'])
def stats(self, request):
    # Calculate rating distribution in format expected by frontend
    rating_distribution = {}
    for i in range(1, 6):  # 1 to 5 stars
        count = reviews.filter(
            rating__gte=i,
            rating__lt=i + 1
        ).count()
        rating_distribution[i] = count

    stats = {
        'total_reviews': reviews.count(),
        'average_rating': float(reviews.aggregate(Avg('rating'))['rating__avg'] or 0),
        'rating_distribution': rating_distribution,  # Format: {1: count, 2: count, ...}
        # ...
    }
```

## 📍 Các Response được sử dụng ở đâu

### 1. **getMovieReviews Response**

**Format:**

```javascript
{
  data: [...],              // Array of reviews
  total_pages: 10,          // Total pages for pagination
  current_page: 1,          // Current page number
  count: 100,               // Total number of reviews
  rating_distribution: {},  // Rating distribution object
  average_rating: 4.2,      // Average rating
  total_ratings: 100        // Total number of ratings
}
```

**Sử dụng tại:**

- `frontend/src/pages/Movies/components/RatingTab.jsx` - Hiển thị danh sách reviews
- `frontend/src/pages/Movies/components/CommentTab.jsx` - Hiển thị comments
- `frontend/src/components/movies/movie-details/ReviewSection.jsx` - Review section

### 2. **getUserReview Response**

**Format:**

```javascript
{
  data: [...],              // Array of user reviews
  results: [...],           // Backward compatibility
  count: 1,                 // Number of reviews
  status: 'success'         // Response status
}
```

**Sử dụng tại:**

- `frontend/src/pages/Movies/components/RatingTab.jsx` - Hiển thị user's own review
- `frontend/src/pages/Movies/components/CommentTab.jsx` - Hiển thị user's own comment

### 3. **getUserRatings Response**

**Format:**

```javascript
{
  results: [...],           // Array of user ratings
  data: [...],              // Same as results
  count: 50,                // Total number of ratings
  next: 'url',              // Next page URL
  previous: 'url',          // Previous page URL
  status: 'success'         // Response status
}
```

**Sử dụng tại:**

- `frontend/src/pages/Profile/components/RatingList.jsx` - Hiển thị user's rating history
- `frontend/src/pages/Profile/index.jsx` - Profile page ratings tab

### 4. **Review Stats Response**

**Format:**

```javascript
{
  total_reviews: 100,
  average_rating: 4.2,
  rating_distribution: {
    1: 5,    // 5 reviews with 1 star
    2: 10,   // 10 reviews with 2 stars
    3: 20,   // 20 reviews with 3 stars
    4: 35,   // 35 reviews with 4 stars
    5: 30    // 30 reviews with 5 stars
  },
  language_distribution: [...],
  recent_reviews: 15
}
```

**Sử dụng tại:**

- `frontend/src/pages/Movies/components/RatingTab.jsx` - Rating overview section
- `frontend/src/components/movies/movie-details/ReviewSection.jsx` - Rating statistics

## 🎯 Lợi ích của việc Standardization

### 1. **Tính nhất quán**

- Tất cả API responses có format tương tự
- Frontend có thể xử lý data một cách nhất quán
- Giảm lỗi do format không đồng nhất

### 2. **Hiệu suất**

- Backend tính toán rating distribution thay vì frontend
- Giảm tải cho frontend khi xử lý large datasets
- Caching có thể được áp dụng ở backend

### 3. **Maintainability**

- Code dễ đọc và maintain hơn
- Giảm duplicate code
- Dễ dàng thêm features mới

### 4. **Backward Compatibility**

- Giữ lại các field cũ để đảm bảo compatibility
- Có thể migrate từ từ mà không break existing code

## 🔄 Migration Guide

### Cho Frontend Developers:

1. Sử dụng standardized API functions từ `movieService.js` và `profileService.js`
2. Cập nhật components để sử dụng new response format
3. Test thoroughly để đảm bảo không có breaking changes

### Cho Backend Developers:

1. Đảm bảo tất cả rating-related APIs trả về format consistent
2. Test rating distribution calculation
3. Monitor performance impact của việc tính toán distribution ở backend

## 📊 Testing Checklist

- [ ] `getMovieReviews` trả về đúng format
- [ ] `getUserReview` trả về đúng format
- [ ] `getUserRatings` trả về đúng format
- [ ] Rating distribution được tính toán đúng
- [ ] Frontend components hiển thị đúng data
- [ ] Pagination hoạt động đúng
- [ ] Error handling hoạt động đúng
- [ ] Backward compatibility được duy trì
