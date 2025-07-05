# Optimized Poster Update Scripts

Script tối ưu hóa chuyên biệt để update poster_url cho movies với performance monitoring và auto-optimization.

## 🚀 Tính năng chính

### 1. **Auto-Optimization**

- Tự động tối ưu batch size dựa trên system resources
- Memory monitoring và auto-clear Redis cache
- CPU và disk usage monitoring
- Adaptive batch processing

### 2. **Performance Monitoring**

- Real-time system resource tracking
- Progress với ETA calculation
- Detailed error categorization
- Memory usage optimization

### 3. **Error Handling**

- Redis connection retry với exponential backoff
- Timeout error handling
- Graceful degradation
- Comprehensive error reporting

## 📁 Files

- `update_missing_posters.py` - Command Django chính với tối ưu hóa
- `run_optimized_poster_update.py` - Script wrapper với auto-optimization
- `run_optimized_poster_update.ps1` - Script PowerShell với system monitoring

## 🎯 Cách sử dụng

### 1. Kiểm tra missing posters

```bash
# Python
python manage.py update_missing_posters --check-only

# PowerShell
.\scripts\run_optimized_poster_update.ps1 -CheckOnly

# Python wrapper
python scripts/run_optimized_poster_update.py --check-only
```

### 2. Chạy với auto-optimization

#### PowerShell (Khuyến nghị)

```powershell
# Auto-optimize batch size
.\scripts\run_optimized_poster_update.ps1

# Custom batch size
.\scripts\run_optimized_poster_update.ps1 -BatchSize 75

# Limit số lượng movies
.\scripts\run_optimized_poster_update.ps1 -Limit 1000

# Start từ movie ID cụ thể
.\scripts\run_optimized_poster_update.ps1 -StartFrom 5000

# Dry run để test
.\scripts\run_optimized_poster_update.ps1 -DryRun
```

#### Python trực tiếp

```bash
# Auto-optimize
python scripts/run_optimized_poster_update.py

# Custom parameters
python scripts/run_optimized_poster_update.py --batch-size 75 --limit 1000

# Django command trực tiếp
python manage.py update_missing_posters --batch-size 50 --memory-limit 500
```

### 3. Advanced Usage

```bash
# Process với retry cao hơn
python manage.py update_missing_posters --batch-size 50 --retry-count 5

# Memory limit thấp hơn
python manage.py update_missing_posters --memory-limit 300

# Start từ movie ID cụ thể
python manage.py update_missing_posters --start-from 10000 --limit 5000
```

## 🔧 Auto-Optimization Logic

### Batch Size Optimization

```python
# Dựa trên system resources
if memory_gb >= 16 and cpu_count >= 8:
    base_batch_size = 100
elif memory_gb >= 8 and cpu_count >= 4:
    base_batch_size = 50
else:
    base_batch_size = 25

# Dựa trên dataset size
if total_movies > 100000:
    batch_size = min(base_batch_size, 50)  # Smaller for large datasets
elif total_movies > 10000:
    batch_size = base_batch_size
else:
    batch_size = min(base_batch_size * 2, 100)  # Larger for small datasets
```

### Memory Management

- Auto-clear Redis cache khi memory > 500MB
- Monitor system memory usage
- Adaptive batch processing
- Memory leak prevention

## 📊 Output Example

```
[2025-07-05 15:30:00] 🎯 Starting optimized poster update...
[2025-07-05 15:30:01] 📊 System Resources:
[2025-07-05 15:30:01]    CPU Usage: 45.2%
[2025-07-05 15:30:01]    Memory Usage: 67.8% (8.5GB / 12.5GB)
[2025-07-05 15:30:01]    Disk Usage: 72.3%
[2025-07-05 15:30:02] 🔧 Optimized batch size: 75 (CPU: 8, Memory: 12.5GB)
[2025-07-05 15:30:02] 📊 Total movies missing posters: 694,703
[2025-07-05 15:30:02] ⚙️  Configuration:
[2025-07-05 15:30:02]    Batch Size: 75
[2025-07-05 15:30:02]    Retry Count: 3
[2025-07-05 15:30:02]    Limit: No limit
[2025-07-05 15:30:02]    Start From: 0
[2025-07-05 15:30:02]    Dry Run: False
[2025-07-05 15:30:03] 🚀 Starting optimized poster update command...
[2025-07-05 15:30:03] 📋 Command: python manage.py update_missing_posters --batch-size 75 --retry-count 3 --memory-limit 500
[2025-07-05 15:30:04] 🚀 Updating poster for 694,703 movies missing poster (96.8%)
[2025-07-05 15:30:15] 📦 Processing batch 1: movies 1-75 of 694,703
[2025-07-05 15:30:25] 📊 Batch 1 Summary:
[2025-07-05 15:30:25]    ✅ Success: 68 | ❌ Errors: 7
[2025-07-05 15:30:25]    🔴 Redis Errors: 0 | ⏰ Timeout: 2
[2025-07-05 15:30:25]    📈 No Poster Found: 5
[2025-07-05 15:30:25] 📊 Overall Progress: 75/694,703 (0.0%)
[2025-07-05 15:30:25]    ✅ Total Success: 68 | ❌ Total Errors: 7
[2025-07-05 15:30:25]    ⏱️  Elapsed: 0.3m | ⏳ ETA: 46.2m
[2025-07-05 15:30:25]    🎯 Success Rate: 90.7%
...
[2025-07-05 16:45:30] ✅ Poster update completed!
[2025-07-05 16:45:30] 📊 Final Summary:
[2025-07-05 16:45:30]    ⏱️  Total Time: 75.5 minutes
[2025-07-05 16:45:30]    📈 Total Processed: 694,703
[2025-07-05 16:45:30]    ✅ Successful: 650,123
[2025-07-05 16:45:30]    ❌ Total Errors: 44,580
[2025-07-05 16:45:30]    🔴 Redis Errors: 1,234
[2025-07-05 16:45:30]    ⏰ Timeout Errors: 5,678
[2025-07-05 16:45:30]    📈 No Poster Found: 37,668
[2025-07-05 16:45:30]    🎯 Success Rate: 93.6%
[2025-07-05 16:45:30]    📊 Avg Time per Movie: 0.65s
[2025-07-05 16:45:30]    📊 Remaining Missing Posters: 37,668
```

## ⚙️ Configuration Options

### Command Line Parameters

- `--batch-size`: Batch size cho processing (auto-optimized nếu không chỉ định)
- `--retry-count`: Số lần retry cho failed operations (default: 3)
- `--memory-limit`: Memory limit MB trước khi clear Redis cache (default: 500)
- `--limit`: Giới hạn số lượng movies xử lý
- `--start-from`: Bắt đầu từ movie ID cụ thể
- `--dry-run`: Chỉ hiển thị sẽ update gì, không thực hiện thay đổi
- `--check-only`: Chỉ kiểm tra số lượng missing posters

### System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB RAM, 4 CPU cores
- **Optimal**: 16GB+ RAM, 8+ CPU cores

## 🔍 Performance Monitoring

### System Resources

- CPU usage monitoring
- Memory usage tracking
- Disk space monitoring
- Network connection status

### Redis Monitoring

- Connection status
- Memory usage
- Auto-clear cache khi cần
- Connection retry logic

### Error Tracking

- Redis connection errors
- Timeout errors
- TMDB API errors
- Network errors
- Memory errors

## 🛠️ Troubleshooting

### 1. High Memory Usage

```bash
# Giảm batch size
python manage.py update_missing_posters --batch-size 25

# Giảm memory limit
python manage.py update_missing_posters --memory-limit 300

# Clear Redis cache manually
python scripts/monitor_redis.py --clear-cache
```

### 2. Slow Performance

```bash
# Tăng batch size (nếu có đủ memory)
python manage.py update_missing_posters --batch-size 100

# Giảm retry count
python manage.py update_missing_posters --retry-count 2

# Process từng phần nhỏ
python manage.py update_missing_posters --limit 1000 --start-from 0
```

### 3. Redis Connection Issues

```bash
# Check Redis status
python scripts/monitor_redis.py --check-only

# Restart Redis service
sudo systemctl restart redis

# Clear Redis cache
python scripts/monitor_redis.py --clear-cache
```

### 4. TMDB API Issues

```bash
# Tăng retry count
python manage.py update_missing_posters --retry-count 5

# Giảm batch size để ít concurrent requests
python manage.py update_missing_posters --batch-size 25
```

## 📈 Performance Tips

1. **Batch Size**:

   - Large datasets (>100k): 25-50
   - Medium datasets (10k-100k): 50-75
   - Small datasets (<10k): 75-100

2. **Memory Management**:

   - Monitor Redis memory usage
   - Clear cache khi >500MB
   - Restart nếu memory leak

3. **Network Optimization**:

   - Use connection pooling
   - Implement proper timeouts
   - Retry với exponential backoff

4. **System Resources**:
   - Monitor CPU usage
   - Check available memory
   - Ensure sufficient disk space

## 🔒 Security Considerations

- Validate TMDB API responses
- Sanitize movie data
- Monitor for suspicious activity
- Regular backup trước khi chạy

## 📝 Log Files

- `optimized_poster_update.log`: Main execution log (temporary)
- `optimized_poster_update_error.log`: Error log (temporary)
- `redis_monitor.log`: Redis monitoring log

## 🤝 Support

Nếu gặp vấn đề:

1. Check system resources
2. Verify Redis connection
3. Review error logs
4. Adjust batch size và retry count
5. Monitor memory usage
