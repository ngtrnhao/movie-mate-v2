# 🚀 Resilient Movie Indexing Guide

## 📋 Tổng Quan

Script `index_movies` đã được cải tiến với khả năng **chống mất kết nối** và **tự động tiếp tục** khi bị gián đoạn. Hệ thống bao gồm:

- ✅ **Retry Logic**: Tự động thử lại khi mất kết nối
- ✅ **Checkpoint System**: Lưu tiến độ và có thể tiếp tục
- ✅ **Connection Resilience**: Xử lý lỗi kết nối Elasticsearch
- ✅ **Progress Monitoring**: Theo dõi tiến độ real-time
- ✅ **Error Recovery**: Khôi phục từ lỗi và tiếp tục

---

## 🔧 Cách Sử Dụng

### **1. Sử dụng Script Wrapper (Khuyên dùng)**

```bash
# Cách sử dụng cơ bản (tương đương với lệnh gốc)
python scripts/run_index_movies_resilient.py --rebuild --verify --all-movies --batch-size 5000

# Kiểm tra kết nối Elasticsearch
python scripts/run_index_movies_resilient.py --check-connection

# Xem thông tin checkpoint
python scripts/run_index_movies_resilient.py --show-checkpoint

# Xóa checkpoint
python scripts/run_index_movies_resilient.py --clear-checkpoint

# Tiếp tục từ checkpoint
python scripts/run_index_movies_resilient.py --resume
```

### **2. Sử dụng Management Command trực tiếp**

```bash
# Lệnh cơ bản với resilience
python manage.py index_movies --rebuild --verify --all-movies --batch-size 5000 --max-retries 5 --retry-delay 2.0

# Tiếp tục từ checkpoint
python manage.py index_movies --resume --all-movies --batch-size 5000

# Tùy chỉnh retry settings
python manage.py index_movies --rebuild --all-movies --max-retries 10 --retry-delay 5.0 --connection-timeout 120
```

---

## 🛡️ Tính Năng Resilience

### **1. Retry Logic**

```python
# Tự động thử lại khi gặp lỗi kết nối
for retry_attempt in range(max_retries + 1):
    try:
        # Thực hiện operation
        bulk_index_operation()
        break
    except (ConnectionError, ConnectionTimeout) as e:
        if retry_attempt < max_retries:
            time.sleep(retry_delay)
            continue
        else:
            # Ghi log lỗi và tiếp tục batch tiếp theo
            log_error_and_continue()
```

**Các loại lỗi được xử lý:**

- `ConnectionError`: Lỗi kết nối mạng
- `ConnectionTimeout`: Timeout kết nối
- `RequestError`: Lỗi request Elasticsearch
- `Exception`: Các lỗi khác

### **2. Checkpoint System**

```json
{
  "last_batch": 50000,
  "indexed_count": 250000,
  "error_count": 150,
  "skipped_count": 500,
  "timestamp": 1640995200,
  "options": {
    "batch_size": 5000,
    "all_movies": true,
    "quality_metrics_only": false,
    "scheduling_only": false,
    "start_id": null,
    "end_id": null,
    "force": false
  }
}
```

**Checkpoint được lưu:**

- Mỗi `checkpoint_interval` batches (mặc định: 10)
- Khi script bị interrupt (Ctrl+C)
- Khi gặp lỗi nghiêm trọng

### **3. Connection Management**

```python
# Kiểm tra kết nối với timeout
def check_elasticsearch_connection():
    for attempt in range(max_retries + 1):
        try:
            es = connections.get_connection()
            health = es.cluster.health(timeout=f"{connection_timeout}s")
            return True
        except (ConnectionError, ConnectionTimeout):
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                return False
```

---

## 📊 Các Tùy Chọn Mới

### **Resilience Options**

| Option                  | Mặc định | Mô tả                          |
| ----------------------- | -------- | ------------------------------ |
| `--max-retries`         | 5        | Số lần thử lại tối đa          |
| `--retry-delay`         | 2.0s     | Thời gian chờ giữa các lần thử |
| `--checkpoint-interval` | 10       | Lưu checkpoint mỗi N batches   |
| `--connection-timeout`  | 60s      | Timeout kết nối Elasticsearch  |
| `--resume`              | False    | Tiếp tục từ checkpoint         |

### **Ví Dụ Sử Dụng**

```bash
# Cấu hình cho mạng chậm
python manage.py index_movies \
    --rebuild --all-movies \
    --max-retries 10 \
    --retry-delay 5.0 \
    --connection-timeout 120 \
    --checkpoint-interval 5

# Cấu hình cho mạng nhanh
python manage.py index_movies \
    --rebuild --all-movies \
    --max-retries 3 \
    --retry-delay 1.0 \
    --connection-timeout 30 \
    --checkpoint-interval 20
```

---

## 🔄 Workflow Khi Bị Gián Đoạn

### **1. Khi Script Bị Dừng (Ctrl+C)**

```bash
# Script sẽ tự động lưu checkpoint
⚠️ Indexing interrupted by user
💾 Checkpoint saved - you can resume with --resume flag

# Tiếp tục chạy
python manage.py index_movies --resume --all-movies --batch-size 5000
```

### **2. Khi Mất Kết Nối Mạng**

```bash
# Script sẽ tự động thử lại
⚠️ Elasticsearch connection attempt 1/6 failed: Connection timeout
⏳ Retrying in 2.0s...
⚠️ Elasticsearch connection attempt 2/6 failed: Connection timeout
⏳ Retrying in 2.0s...
✅ Elasticsearch cluster health: green

# Tiếp tục indexing từ batch hiện tại
```

### **3. Khi Elasticsearch Bị Restart**

```bash
# Script sẽ phát hiện và thử lại
⚠️ Batch 15000-20000 attempt 1/6 failed: Connection refused
⏳ Retrying in 2.0s...
✅ Batch 15000-20000 completed successfully
```

---

## 📈 Monitoring và Logging

### **1. Progress Monitoring**

```bash
📈 Progress: 25.0% (125,000/500,000) -
✅ Indexed: 120,000 |
❌ Errors: 150 |
⏭️ Skipped: 500 |
⏰ ETA: 1800s

💾 Checkpoint saved at batch 50000
```

### **2. Error Logging**

```bash
# Lỗi kết nối
⚠️ Batch 25000-30000 attempt 2/6 failed: Connection timeout

# Lỗi dữ liệu
❌ Error preparing movie 12345: Invalid field value

# Lỗi bulk indexing
❌ Failed to index 5 items in batch
```

### **3. Statistics**

```bash
🎉 Indexing completed in 3600.0s
📊 Final stats:
  ✅ Successfully indexed: 500,000
  ❌ Errors: 1,250
  ⏭️ Skipped: 2,500
  🚀 Rate: 138.9 docs/sec
```

---

## 🛠️ Troubleshooting

### **1. Kiểm Tra Kết Nối**

```bash
# Kiểm tra Elasticsearch
python scripts/run_index_movies_resilient.py --check-connection

# Kết quả mong đợi
✅ Elasticsearch connection: green
```

### **2. Xem Checkpoint**

```bash
# Xem thông tin checkpoint
python scripts/run_index_movies_resilient.py --show-checkpoint

# Kết quả
💾 Found existing checkpoint:
   📊 Last batch: 50,000
   ✅ Indexed: 250,000
   ❌ Errors: 150
   ⏭️ Skipped: 500
   ⏰ Timestamp: 2025-01-15 10:30:00
```

### **3. Xóa Checkpoint**

```bash
# Xóa checkpoint để bắt đầu lại
python scripts/run_index_movies_resilient.py --clear-checkpoint
```

### **4. Lỗi Thường Gặp**

#### **Connection Timeout**

```bash
# Tăng timeout
python manage.py index_movies --connection-timeout 120 --retry-delay 5.0
```

#### **Too Many Retries**

```bash
# Giảm số lần retry
python manage.py index_movies --max-retries 3 --retry-delay 1.0
```

#### **Memory Issues**

```bash
# Giảm batch size
python manage.py index_movies --batch-size 1000 --checkpoint-interval 5
```

---

## 🎯 Best Practices

### **1. Cấu Hình Theo Môi Trường**

#### **Development (Local)**

```bash
python manage.py index_movies \
    --rebuild --all-movies \
    --batch-size 1000 \
    --max-retries 3 \
    --retry-delay 1.0 \
    --connection-timeout 30
```

#### **Production (Remote)**

```bash
python manage.py index_movies \
    --rebuild --all-movies \
    --batch-size 5000 \
    --max-retries 10 \
    --retry-delay 5.0 \
    --connection-timeout 120 \
    --checkpoint-interval 5
```

### **2. Monitoring**

```bash
# Theo dõi tiến độ
watch -n 10 'python scripts/run_index_movies_resilient.py --show-checkpoint'

# Kiểm tra logs
tail -f logs/index_movies.log
```

### **3. Backup và Recovery**

```bash
# Backup checkpoint
cp index_movies_checkpoint.json backup_checkpoint_$(date +%Y%m%d_%H%M%S).json

# Restore checkpoint
cp backup_checkpoint_20250115_103000.json index_movies_checkpoint.json
```

---

## 📊 Performance Metrics

### **1. Expected Performance**

| Batch Size | Retry Delay | Connection Timeout | Expected Rate     |
| ---------- | ----------- | ------------------ | ----------------- |
| 1000       | 1.0s        | 30s                | 200-300 docs/sec  |
| 5000       | 2.0s        | 60s                | 500-800 docs/sec  |
| 10000      | 5.0s        | 120s               | 800-1200 docs/sec |

### **2. Resource Usage**

- **Memory**: ~50-100MB per batch
- **CPU**: 10-20% during indexing
- **Network**: 1-5 MB/s to Elasticsearch
- **Disk**: Minimal (checkpoint file ~1KB)

---

## 🔗 Related Commands

```bash
# Các lệnh liên quan
python manage.py setup_elasticsearch
python manage.py reindex_movies
python manage.py update_missing_posters
python manage.py calculate_quality_scores
```

---

## 📝 Changelog

### **v2.0.0 - Resilient Indexing**

- ✅ Thêm retry logic cho connection errors
- ✅ Thêm checkpoint system
- ✅ Thêm connection timeout handling
- ✅ Thêm progress monitoring
- ✅ Thêm error recovery
- ✅ Thêm script wrapper

### **v1.0.0 - Basic Indexing**

- ✅ Basic movie indexing
- ✅ Batch processing
- ✅ Error handling
- ✅ Progress reporting

---

## 🆘 Support

Nếu gặp vấn đề, hãy:

1. **Kiểm tra logs**: `tail -f logs/index_movies.log`
2. **Kiểm tra kết nối**: `--check-connection`
3. **Xem checkpoint**: `--show-checkpoint`
4. **Xóa checkpoint**: `--clear-checkpoint`
5. **Thử với batch size nhỏ**: `--batch-size 1000`

**Lưu ý**: Script này được thiết kế để **tự động phục hồi** từ hầu hết các lỗi kết nối. Chỉ cần chạy lại với `--resume` flag để tiếp tục!
