# 📊 COLLABORATIVE FILTERING DATABASE ANALYSIS

Bộ script kiểm tra và phân tích database cho thuật toán Collaborative Filtering trong hệ thống MovieMate.

## 🎯 Mục đích

- **Kiểm tra chất lượng dữ liệu** cho CF algorithm
- **Phân tích độ thưa thớt (sparsity)** của ma trận rating
- **Đánh giá vấn đề Cold Start**
- **Tạo báo cáo chi tiết** để cải thiện hệ thống
- **Monitoring hiệu năng** CF algorithm

## 📁 Các Script

### 1. `quick_cf_check.py` - Kiểm tra nhanh

```bash
python scripts/quick_cf_check.py
```

**Chức năng:**

- Thống kê cơ bản (users, movies, ratings)
- Phân phối rating values
- Phân tích Cold Start nhanh
- Đánh giá tổng quan

**Thời gian chạy:** ~5-10 giây

### 2. `check_cf_database.py` - Kiểm tra chi tiết

```bash
python scripts/check_cf_database.py
```

**Chức năng:**

- 10 loại kiểm tra chi tiết
- Phân tích sparsity patterns
- Kiểm tra chất lượng rating
- Test similarity calculation
- Đánh giá performance
- Kiểm tra data consistency

**Thời gian chạy:** ~30-60 giây

### 3. `generate_cf_report.py` - Tạo báo cáo

```bash
python scripts/generate_cf_report.py
```

**Chức năng:**

- Phân tích chi tiết user behavior
- Phân tích movie popularity
- Tạo khuyến nghị cải thiện
- Xuất báo cáo JSON

**Output:** `reports/cf_report_YYYYMMDD_HHMMSS.json`

### 4. `run_cf_analysis.py` - Chạy tất cả

```bash
python scripts/run_cf_analysis.py
```

**Chức năng:**

- Chạy tất cả 3 script trên
- Tạo báo cáo tổng hợp
- Hiển thị kết quả chi tiết

## 📊 Các Chỉ Số Được Phân Tích

### 1. Thống Kê Cơ Bản

- Tổng số users, movies, ratings
- Users/Movies có rating
- Rating trung bình
- Coverage percentage

### 2. Phân Phối Rating

- Phân phối rating values (1-5 sao)
- Số rating per user
- Số rating per movie
- Activity levels

### 3. Sparsity Analysis

- Overall sparsity
- User-level sparsity
- Sparsity patterns
- Impact assessment

### 4. Cold Start Analysis

- Users với <5 ratings
- Movies với <5 ratings
- New users (30 ngày)
- Engagement rate

### 5. Data Quality

- Duplicate ratings
- Invalid ratings
- Suspicious patterns
- Data consistency

### 6. Performance Metrics

- Similarity calculation time
- Recommendation generation time
- Database query performance
- Coverage analysis

## 🎯 Cách Đọc Kết Quả

### Sparsity Levels

- **< 90%**: Tốt - CF hoạt động hiệu quả
- **90-95%**: Trung bình - Cần cải thiện
- **95-99%**: Cao - Cần hybrid approach
- **> 99%**: Rất cao - CF kém hiệu quả

### Cold Start Levels

- **< 25%**: Tốt - Ít vấn đề cold start
- **25-50%**: Trung bình - Cần demographic filtering
- **> 50%**: Cao - Cần cải thiện đáng kể

### Data Quality

- **Duplicate ratings**: Cần data cleaning
- **Invalid ratings**: Cần validation
- **Suspicious patterns**: Cần investigation

## 🚀 Khuyến Nghị Cải Thiện

### 1. Sparsity Cao (>95%)

```
✅ Sử dụng Hybrid approach
✅ Tăng user engagement
✅ Content-based filtering
✅ Demographic filtering
```

### 2. Cold Start Cao (>50%)

```
✅ Demographic filtering cho new users
✅ Popular items recommendation
✅ Onboarding process
✅ Gamification
```

### 3. Data Quality Issues

```
✅ Data cleaning pipeline
✅ Rating validation
✅ Duplicate detection
✅ Suspicious pattern detection
```

### 4. Performance Issues

```
✅ Database optimization
✅ Caching strategies
✅ Query optimization
✅ Indexing
```

## 📈 Monitoring Schedule

### Hàng ngày

```bash
python scripts/quick_cf_check.py
```

### Hàng tuần

```bash
python scripts/check_cf_database.py
```

### Hàng tháng

```bash
python scripts/run_cf_analysis.py
```

## 🔧 Troubleshooting

### Lỗi Import

```bash
# Đảm bảo đang ở thư mục backend
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

### Lỗi Database

```bash
# Kiểm tra database connection
python manage.py dbshell

# Kiểm tra migrations
python manage.py showmigrations
```

### Lỗi Memory

```bash
# Giảm sample size trong scripts
# Thay đổi [:100] thành [:50] trong các queries
```

## 📋 Output Files

### Console Output

- Thống kê real-time
- Cảnh báo issues
- Khuyến nghị cải thiện

### JSON Report

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_users": 1000,
    "total_movies": 5000,
    "total_ratings": 50000,
    "sparsity": 0.99
  },
  "detailed_analysis": {
    "sparsity": {...},
    "cold_start": {...},
    "performance": {...}
  },
  "recommendations": [
    {
      "priority": "high",
      "issue": "Sparsity cao",
      "recommendation": "Sử dụng hybrid approach"
    }
  ]
}
```

## 🤝 Contributing

Để thêm tính năng mới:

1. Tạo script mới trong thư mục `scripts/`
2. Thêm vào `run_cf_analysis.py`
3. Cập nhật README này
4. Test với database thực tế

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra logs trong console
2. Xem file JSON report
3. Kiểm tra database connection
4. Liên hệ team development
