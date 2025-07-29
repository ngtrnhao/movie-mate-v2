# Vietnamese Movie Import Commands

Hướng dẫn sử dụng các commands để import phim tiếng Việt từ TMDB API.

## Tổng quan

Dự án cung cấp 2 commands chính để import phim Việt Nam:

1. **`import_vietnamese_movies`** - Import phim Việt Nam theo năm sử dụng API `with_original_language=vi`
2. **`search_vietnamese_movies`** - Tìm kiếm phim Việt Nam bằng từ khóa và bộ lọc

### 🎯 **API Mới Hiệu Quả**

Commands sử dụng API endpoint mới:

```
https://api.themoviedb.org/3/discover/movie?with_original_language=vi
```

API này trả về **1251 phim tiếng Việt** với thông tin đầy đủ, bao gồm:

- Original title tiếng Việt
- English title
- Overview
- Ratings và vote counts
- Release dates
- Genre IDs
- Poster và backdrop paths

## Yêu cầu

### 1. TMDB API Key

Bạn cần có TMDB API key để sử dụng các commands này:

1. Đăng ký tài khoản tại: https://www.themoviedb.org/
2. Vào Settings > API
3. Tạo API key mới
4. Thêm vào file `.env.local`:
   ```
   TMDB_API_KEY=your_api_key_here
   ```

### 2. Cài đặt dependencies

```bash
pip install requests
```

## Command 1: import_vietnamese_movies

Command này import phim Việt Nam theo năm và region từ TMDB.

### Cách sử dụng cơ bản:

```bash
# Import với cài đặt mặc định (2010-2024, max 1000 phim)
python manage.py import_vietnamese_movies

# Import với API key từ command line
python manage.py import_vietnamese_movies --tmdb-api-key=your_key

# Import với tùy chọn tùy chỉnh
python manage.py import_vietnamese_movies \
    --max-movies=500 \
    --year-from=2015 \
    --year-to=2024 \
    --min-rating=6.0 \
    --batch-size=10
```

### Các tùy chọn:

- `--tmdb-api-key`: TMDB API key (nếu không có trong .env.local)
- `--max-movies`: Số lượng phim tối đa import (mặc định: 1000)
- `--batch-size`: Kích thước batch xử lý (mặc định: 20)
- `--year-from`: Năm bắt đầu tìm kiếm (mặc định: 2010)
- `--year-to`: Năm kết thúc tìm kiếm (mặc định: 2024)
- `--min-rating`: Rating tối thiểu để import (mặc định: 5.0)
- `--include-adult`: Bao gồm phim người lớn
- `--dry-run`: Chạy thử không lưu dữ liệu
- `--update-existing`: Cập nhật phim đã tồn tại
- `--region`: Mã region (mặc định: VN)
- `--language`: Ngôn ngữ chính (mặc định: vi-VN)

### Ví dụ sử dụng:

```bash
# Import phim Việt Nam từ 2015-2024, rating >= 6.0
python manage.py import_vietnamese_movies \
    --year-from=2015 \
    --year-to=2024 \
    --min-rating=6.0 \
    --max-movies=200

# Chạy thử để xem sẽ import những phim nào
python manage.py import_vietnamese_movies --dry-run --max-movies=50

# Import và cập nhật phim đã tồn tại
python manage.py import_vietnamese_movies --update-existing --max-movies=100
```

## Command 2: search_vietnamese_movies

Command này tìm kiếm phim Việt Nam bằng nhiều phương pháp khác nhau.

### Cách sử dụng cơ bản:

```bash
# Tìm kiếm với cài đặt mặc định
python manage.py search_vietnamese_movies

# Tìm kiếm với từ khóa tùy chỉnh
python manage.py search_vietnamese_movies \
    --search-keywords="vietnam,việt nam,saigon,hanoi,đà nẵng"
```

### Các tùy chọn:

- `--tmdb-api-key`: TMDB API key
- `--max-movies`: Số lượng phim tối đa import (mặc định: 500)
- `--batch-size`: Kích thước batch xử lý (mặc định: 10)
- `--year-from`: Năm bắt đầu tìm kiếm (mặc định: 1990)
- `--year-to`: Năm kết thúc tìm kiếm (mặc định: 2024)
- `--min-rating`: Rating tối thiểu để import (mặc định: 4.0)
- `--dry-run`: Chạy thử không lưu dữ liệu
- `--update-existing`: Cập nhật phim đã tồn tại
- `--search-keywords`: Từ khóa tìm kiếm (mặc định: "vietnam,vietnamese,việt nam,việt,saigon,hanoi")
- `--include-adult`: Bao gồm phim người lớn

### Phương pháp tìm kiếm:

Command này sử dụng 4 phương pháp tìm kiếm:

1. **Tìm kiếm theo từ khóa**: Tìm phim có chứa từ khóa Việt Nam
2. **Tìm kiếm theo region**: Tìm phim từ region VN
3. **Tìm kiếm theo ngôn ngữ**: Tìm phim có ngôn ngữ gốc tiếng Việt (sử dụng API `with_original_language=vi`)
4. **Tìm kiếm theo công ty sản xuất**: Tìm phim của các công ty Việt Nam

### 🚀 **Cải tiến mới:**

- **API chính**: Sử dụng `with_original_language=vi` để lấy chính xác phim tiếng Việt
- **Pagination**: Tự động lấy nhiều trang để có đầy đủ dữ liệu
- **Rate limiting**: Tự động xử lý rate limiting của TMDB
- **Thông tin chi tiết**: Lấy thêm credits, videos, và metadata đầy đủ

### Ví dụ sử dụng:

```bash
# Tìm kiếm với từ khóa tùy chỉnh
python manage.py search_vietnamese_movies \
    --search-keywords="vietnam,việt nam,saigon,hanoi,đà nẵng,huế" \
    --max-movies=100

# Tìm kiếm phim cũ hơn (1990-2010)
python manage.py search_vietnamese_movies \
    --year-from=1990 \
    --year-to=2010 \
    --min-rating=3.0

# Chạy thử tìm kiếm
python manage.py search_vietnamese_movies --dry-run --max-movies=20
```

## Dữ liệu được import

Cả hai commands đều import các thông tin sau:

### Thông tin cơ bản:

- Title (tiếng Anh và tiếng Việt)
- Original title tiếng Việt
- Release date
- Runtime
- Status
- Poster và backdrop URLs

### Ratings:

- TMDB rating và vote count
- Combined rating score

### Metadata:

- Budget và revenue
- Production companies
- Production countries
- Spoken languages
- Tagline và homepage

### Genres:

- Tự động tạo và liên kết genres
- Hỗ trợ đa ngôn ngữ

### Cast & Crew:

- Diễn viên chính (top 10)
- Đạo diễn, biên kịch, nhà sản xuất
- Thông tin profile và popularity

### Videos:

- Trailers và clips
- YouTube keys

## Xử lý đa ngôn ngữ

Commands tự động xử lý nội dung đa ngôn ngữ:

1. **Title**: Lưu cả tiếng Anh (`title_en`) và tiếng Việt (`title_vi`)
2. **Overview**: Lưu cả tiếng Anh (`overview_en`) và tiếng Việt (`overview_vi`)
3. **Genres**: Tạo genres với language field
4. **Fallback**: Sử dụng tiếng Anh làm fallback nếu không có tiếng Việt

## Rate Limiting

Commands tự động xử lý rate limiting của TMDB API:

- Delay 0.25 giây giữa các requests
- Retry mechanism với exponential backoff
- Cache responses để giảm API calls

## Logging và Monitoring

Commands cung cấp thông tin chi tiết:

- Progress updates
- Import statistics
- Error logging
- Success/failure counts

## Troubleshooting

### Lỗi thường gặp:

1. **"TMDB API key required"**

   - Kiểm tra file `.env.local` có chứa `TMDB_API_KEY`
   - Hoặc sử dụng `--tmdb-api-key` parameter

2. **"Rate limit exceeded"**

   - Commands tự động xử lý, nhưng có thể chậm
   - Giảm `--batch-size` nếu cần

3. **"No movies found"**
   - Thử điều chỉnh `--min-rating` thấp hơn
   - Mở rộng range năm với `--year-from` và `--year-to`
   - Thêm từ khóa tìm kiếm với `--search-keywords`

### Tips:

1. **Bắt đầu với dry-run**: Luôn test với `--dry-run` trước
2. **Bắt đầu nhỏ**: Sử dụng `--max-movies=10` để test
3. **Kiểm tra logs**: Xem logs để debug issues
4. **Update existing**: Sử dụng `--update-existing` để cập nhật phim đã có

## Kết quả mong đợi

Sau khi chạy commands, bạn sẽ có:

1. **Movies table**: Phim với thông tin đầy đủ
2. **Genres table**: Genres được tạo tự động
3. **MovieMetadata table**: Metadata chi tiết
4. **MovieRating table**: Ratings từ TMDB
5. **MovieGenre table**: Liên kết phim-genre

Tất cả phim sẽ có:

- Title và overview bằng cả tiếng Anh và tiếng Việt
- Poster và backdrop images
- Ratings và metadata đầy đủ
- Genres được phân loại chính xác
