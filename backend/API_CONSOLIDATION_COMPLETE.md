# API Consolidation Summary - Movie Recommendation System

## Tổng quan thay đổi

Đã hoàn thành việc **hợp nhất và đồng bộ hóa API endpoints** từ 2 ViewSet riêng biệt (`MovieReviewViewSet` và `OptimizedMovieViewSet`) thành 1 ViewSet thống nhất (`OptimizedMovieViewSet`) với prefix **`/api/movies/`** duy nhất.

## Vấn đề đã giải quyết

1. **Logic trùng lặp**: Trước đây có 2 ViewSet xử lý review với logic tương tự nhau
2. **Endpoint không đồng nhất**: Frontend gọi cả `/api/movies/` và `/api/reviews/`
3. **Spoiler detection không nhất quán**: Logic được implement khác nhau ở 2 nơi
4. **Response format khác nhau**: Các endpoint trả về format khác nhau

## Các thay đổi Backend

### 1. OptimizedMovieViewSet - Actions được thêm mới:

```python
# Review actions
- stats(movie_id)                     # GET /api/movies/stats/
- vote_review(review_id, vote)        # POST /api/movies/reviews/vote/
- my_reviews(movie_id?, page, size)   # GET /api/movies/reviews/my/
- reply_to_review(parent_review_id)   # POST /api/movies/reviews/reply/
- review_replies(review_id, page)     # GET /api/movies/reviews/replies/

# Spoiler detection
- detect_spoilers(content, language)  # POST /api/movies/reviews/detect_spoilers/

# Moderation actions
- moderation_queue(page, filters)     # GET /api/movies/reviews/moderation_queue/
- moderation_stats()                  # GET /api/movies/reviews/moderation_stats/
- moderate_review(review_id, action)  # POST /api/movies/reviews/moderate/
- bulk_moderate(review_ids, action)   # POST /api/movies/reviews/bulk_moderate/
- update_task_status(task_id, status) # POST /api/movies/reviews/update_task_status/
```

### 2. URL Configuration - Consolidated under `/api/movies/`:

```python
# Movie list actions
/api/movies/featured/
/api/movies/trending/
/api/movies/top_rated/
/api/movies/upcoming/
/api/movies/search/
/api/movies/search_suggestions/
/api/movies/stats/

# Movie detail actions
/api/movies/{id}/
/api/movies/{id}/reviews/     # GET, POST
/api/movies/{id}/cast/
/api/movies/{id}/details_complete/

# Review actions (consolidated)
/api/movies/reviews/my/
/api/movies/reviews/vote/
/api/movies/reviews/reply/
/api/movies/reviews/replies/
/api/movies/reviews/detect_spoilers/

# Moderation actions (consolidated)
/api/movies/reviews/moderation_queue/
/api/movies/reviews/moderation_stats/
/api/movies/reviews/moderate/
/api/movies/reviews/bulk_moderate/
/api/movies/reviews/update_task_status/
```

### 3. Deleted/Removed:

- `MovieReviewViewSet` class (hoàn toàn bị xóa)
- Các URL mapping cũ với prefix `/api/reviews/`
- Logic trùng lặp trong spoiler detection

## Các thay đổi Frontend

### 1. API Service Functions - Updated endpoints:

```javascript
// Review functions
submitMovieReview(movieId, reviewData)       # POST /api/movies/{id}/reviews/
getMovieReviews(movieId, page, limit, sort)  # GET /api/movies/{id}/reviews/
getMovieStats(movieId)                       # GET /api/movies/stats/
voteOnReview(reviewId, voteType)            # POST /api/movies/reviews/vote/
getMyReviews(movieId?, page, size)          # GET /api/movies/reviews/my/

// Reply functions
replyToReview(reviewId, replyData)          # POST /api/movies/reviews/reply/
getReviewReplies(reviewId, page, size)      # GET /api/movies/reviews/replies/

// Spoiler detection
detectSpoilers(content, language, title)    # POST /api/movies/reviews/detect_spoilers/

// Moderation functions
getModerationQueue(page, filters)           # GET /api/movies/reviews/moderation_queue/
getModerationStats()                        # GET /api/movies/reviews/moderation_stats/
moderateReview(reviewId, action, reason)    # POST /api/movies/reviews/moderate/
bulkModerateReviews(ids, action, reason)    # POST /api/movies/reviews/bulk_moderate/
updateTaskStatus(taskId, status)            # POST /api/movies/reviews/update_task_status/
```

### 2. Backward Compatibility:

- `updateMovieReview()` và `deleteMovieReview()` vẫn sử dụng `/api/reviews/{id}/` (để tương thích)
- Các endpoint còn lại đã chuyển sang `/api/movies/` prefix

## API Mapping Table

| Frontend Function       | Old Endpoint                       | New Endpoint                              | Status       |
| ----------------------- | ---------------------------------- | ----------------------------------------- | ------------ |
| `submitMovieReview()`   | `/api/movies/{id}/reviews/`        | `/api/movies/{id}/reviews/`               | ✅ No change |
| `getMovieReviews()`     | `/api/movies/{id}/reviews/`        | `/api/movies/{id}/reviews/`               | ✅ No change |
| `voteOnReview()`        | `/api/reviews/{id}/vote/`          | `/api/movies/reviews/vote/`               | ✅ Updated   |
| `getMyReviews()`        | `/api/reviews/my_reviews/`         | `/api/movies/reviews/my/`                 | ✅ Updated   |
| `replyToReview()`       | `/api/reviews/{id}/reply/`         | `/api/movies/reviews/reply/`              | ✅ Updated   |
| `getReviewReplies()`    | `/api/reviews/{id}/replies/`       | `/api/movies/reviews/replies/`            | ✅ Updated   |
| `detectSpoilers()`      | `/api/reviews/detect_spoilers/`    | `/api/movies/reviews/detect_spoilers/`    | ✅ Updated   |
| `getModerationQueue()`  | `/api/reviews/moderation_queue/`   | `/api/movies/reviews/moderation_queue/`   | ✅ Updated   |
| `moderateReview()`      | `/api/reviews/{id}/moderate/`      | `/api/movies/reviews/moderate/`           | ✅ Updated   |
| `bulkModerateReviews()` | `/api/reviews/bulk_moderate/`      | `/api/movies/reviews/bulk_moderate/`      | ✅ Updated   |
| `updateTaskStatus()`    | `/api/reviews/update_task_status/` | `/api/movies/reviews/update_task_status/` | ✅ Updated   |
| `getModerationStats()`  | `/api/reviews/moderation_stats/`   | `/api/movies/reviews/moderation_stats/`   | ✅ Updated   |

## Lợi ích sau khi consolidation

1. **Đơn giản hóa cấu trúc**: Chỉ còn 1 ViewSet thay vì 2
2. **Endpoint thống nhất**: Tất cả đều dùng prefix `/api/movies/`
3. **Logic spoiler nhất quán**: Sử dụng chung service method
4. **Dễ maintain**: Không còn code trùng lặp
5. **Response format đồng nhất**: Tất cả endpoint trả về format giống nhau

## Testing Required

1. **Functional testing**: Đảm bảo tất cả API hoạt động đúng
2. **Frontend integration**: Kiểm tra tất cả component sử dụng API
3. **Permission testing**: Verify moderator/admin permissions
4. **Error handling**: Test error responses

## Notes

- File `ReviewReportViewSet` vẫn được giữ nguyên vì không conflict
- Các endpoint legacy (update/delete by review ID) vẫn hoạt động để tương thích
- Spoiler detection logic đã được chuẩn hóa và áp dụng đồng nhất

---

**Hoàn thành**: ✅ API consolidation đã được thực hiện thành công
**Thời gian**: Tất cả thay đổi đã được apply
**Status**: Ready for testing
