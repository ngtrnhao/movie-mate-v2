# Poster Update Scripts với Redis Monitoring

Bộ script này giúp cập nhật poster cho movies với monitoring Redis connection và xử lý lỗi tự động.

## 📁 Files

- `update_top_movies.py` - Command Django chính với log real-time và retry mechanism
- `monitor_redis.py` - Script monitor Redis connection và auto-restart
- `run_poster_update_with_monitoring.py` - Script Python chạy poster update với monitoring
- `run_poster_update.bat` - Script batch cho Windows
- `run_poster_update.ps1` - Script PowerShell cho Windows (khuyến nghị)

## 🚀 Cách sử dụng

### 1. Kiểm tra Redis connection

```bash
# Python
python scripts/monitor_redis.py --check-only

# PowerShell
.\scripts\run_poster_update.ps1 -CheckRedisOnly

# Batch
python scripts\monitor_redis.py --check-only
```

### 2. Chạy poster update với monitoring

#### PowerShell (Khuyến nghị)

```powershell
# Chạy với tham số mặc định
.\scripts\run_poster_update.ps1

# Chạy với batch size và retry count tùy chỉnh
.\scripts\run_poster_update.ps1 -BatchSize 50 -RetryCount 3

# Chạy với verbose mode
.\scripts\run_poster_update.ps1 -Verbose
```

#### Batch (Windows)

```cmd
# Chạy với tham số mặc định
scripts\run_poster_update.bat

# Chạy với batch size và retry count tùy chỉnh
scripts\run_poster_update.bat 50 3
```

#### Python trực tiếp

```bash
# Chạy command Django trực tiếp
python manage.py update_top_movies --update-missing-poster --batch-size 100 --retry-count 5

# Chạy với script monitoring
python scripts/run_poster_update_with_monitoring.py --batch-size 100 --retry-count 5
```

### 3. Monitor Redis liên tục

```bash
# Monitor Redis với interval 30s, max 3 failures
python scripts/monitor_redis.py --interval 30 --max-failures 3

# Monitor Redis với interval 10s, max 2 failures
python scripts/monitor_redis.py --interval 10 --max-failures 2
```

## 🔧 Tính năng

### 1. Log Real-time với Timestamp

- Tất cả log đều có timestamp chính xác
- Phân loại log theo level (Info, Warning, Error, Success)
- Hiển thị progress chi tiết với ETA

### 2. Redis Connection Monitoring

- Tự động kiểm tra Redis connection
- Auto-restart Redis service nếu cần
- Memory usage monitoring
- Connection retry với exponential backoff

### 3. Error Handling & Retry

- Retry mechanism cho TMDB API calls
- Xử lý timeout errors
- Phân loại lỗi (Redis, Timeout, General)
- Graceful shutdown với signal handling

### 4. Performance Tracking

- Thời gian xử lý trung bình per movie
- Success rate tracking
- Memory usage monitoring
- Progress với ETA

## 📊 Output Example

```
[2025-07-05 15:30:00] 🎯 Starting poster update with Redis monitoring...
[2025-07-05 15:30:01] 🔍 Checking Redis connection...
[2025-07-05 15:30:01] ✅ Redis connection: OK
[2025-07-05 15:30:02] 🚀 Starting poster update command...
[2025-07-05 15:30:02] 🚀 Updating poster for 694,703 movies missing poster out of 717,980 (96.8%)
[2025-07-05 15:30:15] 📊 Progress: 100/694,703 (0.0%)
[2025-07-05 15:30:15]    ✅ Success: 85 | ❌ Errors: 15
[2025-07-05 15:30:15]    ⏱️  Elapsed: 0.2m | ⏳ ETA: 23.1m
[2025-07-05 15:30:15]    🎯 Success Rate: 85.0%
[2025-07-05 15:30:30] 📊 Progress: 200/694,703 (0.0%)
[2025-07-05 15:30:30]    ✅ Success: 175 | ❌ Errors: 25
[2025-07-05 15:30:30]    ⏱️  Elapsed: 0.5m | ⏳ ETA: 22.8m
[2025-07-05 15:30:30]    🎯 Success Rate: 87.5%
...
[2025-07-05 16:45:30] ✅ Poster update completed!
[2025-07-05 16:45:30] 📊 Final Summary:
[2025-07-05 16:45:30]    ⏱️  Total Time: 75.5 minutes
[2025-07-05 16:45:30]    ✅ Successful: 650,123
[2025-07-05 16:45:30]    ❌ Total Errors: 44,580
[2025-07-05 16:45:30]    🔴 Redis Errors: 1,234
[2025-07-05 16:45:30]    ⏰ Timeout Errors: 5,678
[2025-07-05 16:45:30]    🎯 Success Rate: 93.6%
[2025-07-05 16:45:30]    📈 Avg Time per Movie: 0.65s
```

## ⚠️ Troubleshooting

### 1. Redis Connection Errors

```bash
# Kiểm tra Redis service
sudo systemctl status redis
sudo systemctl restart redis

# Kiểm tra Redis connection
python scripts/monitor_redis.py --check-only
```

### 2. Memory Issues

```bash
# Clear Redis cache
python scripts/monitor_redis.py --clear-cache

# Check Redis memory usage
python scripts/monitor_redis.py --check-only
```

### 3. Permission Issues

```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run as Administrator nếu cần
Start-Process PowerShell -Verb RunAs
```

### 4. Virtual Environment Issues

```bash
# Tạo virtual environment mới
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install requirements
pip install -r requirements/local.txt
```

## 🔧 Configuration

### Environment Variables

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_password

# TMDB API
TMDB_API_KEY=your_tmdb_api_key

# Django settings
DJANGO_SETTINGS_MODULE=config.settings.local
```

### Script Parameters

- `--batch-size`: Số lượng movies xử lý mỗi batch (default: 100)
- `--retry-count`: Số lần retry cho failed operations (default: 5)
- `--interval`: Interval kiểm tra Redis (default: 30s)
- `--max-failures`: Số lần fail tối đa trước khi restart Redis (default: 3)

## 📈 Performance Tips

1. **Batch Size**: Tăng batch size để xử lý nhanh hơn, nhưng có thể gây memory issues
2. **Retry Count**: Tăng retry count để handle network issues tốt hơn
3. **Redis Memory**: Monitor Redis memory usage để tránh OOM
4. **Network**: Sử dụng connection pooling và timeout settings phù hợp

## 🛡️ Security

- Không commit API keys vào git
- Sử dụng environment variables cho sensitive data
- Monitor Redis access logs
- Regular backup Redis data

## 📝 Log Files

- `redis_monitor.log`: Redis monitoring logs
- `poster_update.log`: Poster update progress (temporary)
- `poster_update_error.log`: Error logs (temporary)

## 🤝 Support

Nếu gặp vấn đề, hãy:

1. Kiểm tra log files
2. Chạy với `--verbose` flag
3. Kiểm tra Redis connection
4. Verify environment setup
