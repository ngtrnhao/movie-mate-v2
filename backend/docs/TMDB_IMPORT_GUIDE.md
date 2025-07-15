# TMDB Reviews Import Guide

## 🎬 **Tổng quan**

Import reviews từ TMDB API với mapping hoàn hảo TMDB ID và hỗ trợ IMDB ID mapping.

### ✨ **Tính năng chính:**

- ✅ **Perfect TMDB ID mapping** - Reviews từ TMDB API
- ✅ **IMDB ID mapping** - Tìm TMDB ID qua IMDB ID
- ✅ **Synthetic users** - Tạo user cho user-based features
- ✅ **External reviews** - Reviews không có user (tiết kiệm DB)
- ✅ **3 modes** - Popular, Top Rated, All Movies
- ✅ **Rate limiting** - Tránh API quota limit

---

## 🔧 **Cài đặt**

### **1. TMDB API Key**

Thêm vào file `.env.local`:

```bash
TMDB_API_KEY=your_tmdb_api_key_here
```

### **2. Lấy API Key miễn phí**

- Truy cập: https://www.themoviedb.org/settings/api
- Đăng ký tài khoản miễn phí
- Tạo API key

---

## 📋 **Các tham số**

| Tham số                    | Mô tả                      | Mặc định          |
| -------------------------- | -------------------------- | ----------------- |
| `--tmdb-api-key`           | TMDB API key (optional)    | Lấy từ .env.local |
| `--max-reviews`            | Giới hạn số reviews import | 1000              |
| `--batch-size`             | Số reviews xử lý mỗi batch | 50                |
| `--popular-movies-only`    | Chỉ movies popular         | False             |
| `--top-rated-movies-only`  | Chỉ movies top rated       | False             |
| `--all-movies`             | Tất cả movies              | False             |
| `--include-imdb-mapping`   | Tìm TMDB ID qua IMDB ID    | False             |
| `--create-synthetic-users` | Tạo user cho reviewers     | False             |

---

## 🎯 **1. POPULAR MOVIES**

### **Chỉ TMDB ID:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --create-synthetic-users
```

### **TMDB + IMDB mapping:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --include-imdb-mapping --create-synthetic-users
```

### **Với giới hạn reviews:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --max-reviews 200 --create-synthetic-users
```

### **Với batch size nhỏ:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --batch-size 25 --create-synthetic-users
```

### **Đầy đủ tùy chọn:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --include-imdb-mapping --max-reviews 300 --batch-size 30 --create-synthetic-users
```

**Giới hạn:** 50 movies (`is_popular=True`)

---

## 🏆 **2. TOP RATED MOVIES**

### **Chỉ TMDB ID:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --create-synthetic-users
```

### **TMDB + IMDB mapping:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --include-imdb-mapping --create-synthetic-users
```

### **Với giới hạn reviews:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --max-reviews 200 --create-synthetic-users
```

### **Với batch size nhỏ:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --batch-size 25 --create-synthetic-users
```

### **Đầy đủ tùy chọn:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --include-imdb-mapping --max-reviews 300 --batch-size 30 --create-synthetic-users
```

**Giới hạn:** 50 movies (`is_top_rated=True`)

---

## 🌍 **3. ALL MOVIES**

### **Chỉ TMDB ID:**

```bash
python manage.py import_tmdb_reviews --all-movies --create-synthetic-users
```

### **TMDB + IMDB mapping:**

```bash
python manage.py import_tmdb_reviews --all-movies --include-imdb-mapping --create-synthetic-users
```

### **Với giới hạn reviews:**

```bash
python manage.py import_tmdb_reviews --all-movies --max-reviews 500 --create-synthetic-users
```

### **Với batch size nhỏ:**

```bash
python manage.py import_tmdb_reviews --all-movies --batch-size 25 --create-synthetic-users
```

### **Đầy đủ tùy chọn:**

```bash
python manage.py import_tmdb_reviews --all-movies --include-imdb-mapping --max-reviews 1000 --batch-size 50 --create-synthetic-users
```

**Giới hạn:** 1000 movies (tất cả có TMDB/IMDB ID)

---

## 📽️ **4. DEFAULT (không chọn mode)**

### **Chỉ TMDB ID:**

```bash
python manage.py import_tmdb_reviews --create-synthetic-users
```

### **TMDB + IMDB mapping:**

```bash
python manage.py import_tmdb_reviews --include-imdb-mapping --create-synthetic-users
```

### **Với giới hạn reviews:**

```bash
python manage.py import_tmdb_reviews --max-reviews 200 --create-synthetic-users
```

### **Đầy đủ tùy chọn:**

```bash
python manage.py import_tmdb_reviews --include-imdb-mapping --max-reviews 300 --batch-size 30 --create-synthetic-users
```

**Giới hạn:** 500 movies (mặc định)

---

## 👥 **5. KHÔNG TẠO SYNTHETIC USERS (EXTERNAL reviews)**

### **Popular movies:**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --include-imdb-mapping
```

### **Top rated movies:**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --include-imdb-mapping
```

### **All movies:**

```bash
python manage.py import_tmdb_reviews --all-movies --include-imdb-mapping
```

**Lưu ý:** Không có `--create-synthetic-users` = EXTERNAL reviews (tiết kiệm DB)

---

## 🧪 **6. LỆNH TEST KHUYẾN NGHỊ**

### **Test nhỏ (10 reviews):**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --max-reviews 10 --create-synthetic-users
```

### **Test vừa (50 reviews):**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --include-imdb-mapping --max-reviews 50 --create-synthetic-users
```

### **Test lớn (200 reviews):**

```bash
python manage.py import_tmdb_reviews --all-movies --include-imdb-mapping --max-reviews 200 --batch-size 25 --create-synthetic-users
```

---

## 📊 **7. KẾT QUẢ HIỂN THỊ**

### **Thành công:**

```
🎬 Starting TMDB reviews import...
API Key: 4c338e3a...6df1
Max reviews: 100
Popular only: True
Top rated only: False
All movies: False
Include IMDB mapping: True
Create synthetic users: True
🎯 Mode: Popular movies (TMDB + IMDB mapping)
📽️ Found 75 movies with TMDB/IMDB IDs
🎬 Processing: The Shawshank Redemption (TMDB: 278)
🎬 Processing: The Godfather (IMDB: tt0068646 → TMDB: 238)
✅ The Shawshank Redemption: 4 imported, 0 skipped, 0 errors
✅ TMDB Import completed!
📈 Total imported: 30
⚠️  Skipped: 0
❌ Errors: 2
```

### **Lỗi thường gặp:**

```
⚠️  No reviews found for Movie Title
⚠️  No TMDB ID found for Movie Title (IMDB: tt1234567)
❌ Error: duplicate key value violates unique constraint
```

---

## 🔍 **8. LOGIC HOẠT ĐỘNG**

### **Tìm kiếm movies:**

```python
# Chỉ TMDB ID
movies = Movie.objects.filter(tmdb_id__isnull=False)

# TMDB + IMDB ID
movies = Movie.objects.filter(
    models.Q(tmdb_id__isnull=False) | models.Q(imdb_id__isnull=False)
)
```

### **Xử lý ID:**

```python
# 1. Có TMDB ID → Dùng trực tiếp
if movie.tmdb_id:
    tmdb_id = movie.tmdb_id

# 2. Không có TMDB ID nhưng có IMDB ID → Tìm qua API
elif movie.imdb_id:
    tmdb_id = find_tmdb_id_by_imdb(movie.imdb_id, api_key)

# 3. Không có cả hai → Bỏ qua
else:
    continue
```

### **Review types:**

```python
# Với --create-synthetic-users
review_type = 'USER'      # Có user, không có external_username
user = synthetic_user
external_username = None

# Không có --create-synthetic-users
review_type = 'EXTERNAL'  # Không có user, có external_username
user = None
external_username = author
```

---

## ⚠️ **9. LƯU Ý QUAN TRỌNG**

### **Rate Limiting:**

- TMDB API có giới hạn 40 requests/10 seconds
- Command tự động delay 0.5s giữa các requests
- Không chạy nhiều instances cùng lúc

### **Database Constraints:**

- `review_user_xor_external`: User XOR external_username
- `unique_user_movie_review`: 1 user = 1 review/movie
- `external_review_must_have_id`: EXTERNAL reviews phải có external_review_id

### **Performance:**

- **Synthetic users**: Tạo nhiều user → DB lớn hơn
- **External reviews**: Không tạo user → Tiết kiệm DB
- **IMDB mapping**: Thêm API calls → Chậm hơn

### **Recommendations:**

- **Test nhỏ** trước khi chạy lớn
- **Dùng IMDB mapping** để có nhiều movies hơn
- **Chọn mode phù hợp** với nhu cầu
- **Monitor logs** để tránh lỗi

---

## 🚀 **10. WORKFLOW KHUYẾN NGHỊ**

### **Bước 1: Test nhỏ**

```bash
python manage.py import_tmdb_reviews --popular-movies-only --max-reviews 10 --create-synthetic-users
```

### **Bước 2: Test vừa**

```bash
python manage.py import_tmdb_reviews --top-rated-movies-only --include-imdb-mapping --max-reviews 50 --create-synthetic-users
```

### **Bước 3: Chạy production**

```bash
python manage.py import_tmdb_reviews --all-movies --include-imdb-mapping --max-reviews 1000 --batch-size 50 --create-synthetic-users
```

---

## 📞 **11. TROUBLESHOOTING**

### **Lỗi API Key:**

```
❌ TMDB API key required!
💡 Options:
   1. Add TMDB_API_KEY=your_key to .env.local
   2. Use --tmdb-api-key=your_key command line argument
   3. Get free API key from: https://www.themoviedb.org/settings/api
```

### **Lỗi Duplicate:**

```
ERROR: duplicate key value violates unique constraint "unique_user_movie_review"
```

**Giải pháp:** Command tự động skip duplicates

### **Lỗi Rate Limit:**

```
ERROR: TMDB API error: 429 Too Many Requests
```

**Giải pháp:** Đợi và chạy lại, hoặc giảm batch size

### **Ít reviews:**

```
⚠️  No reviews found for Movie Title
```

**Giải pháp:** Dùng `--include-imdb-mapping` để có nhiều movies hơn

---

## 📈 **12. STATISTICS**

### **Typical Results:**

- **Popular movies**: 30-50 reviews từ 50 movies
- **Top rated movies**: 40-60 reviews từ 50 movies
- **All movies**: 200-500 reviews từ 1000 movies
- **IMDB mapping**: Tăng 20-30% số movies

### **Performance:**

- **Speed**: ~2 requests/second (rate limited)
- **Memory**: Thấp (batch processing)
- **Database**: Tùy theo synthetic users

---

**�� Happy importing!**
