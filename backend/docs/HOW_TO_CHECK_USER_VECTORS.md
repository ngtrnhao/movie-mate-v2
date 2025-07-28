# 🔍 **Hướng Dẫn Kiểm Tra Vector Của Người Dùng**

## 📋 **Tóm tắt**

Để kiểm tra vector của người dùng có được xử lý đúng không, bạn có thể sử dụng các phương pháp sau:

## 🧪 **Phương Pháp 1: Test Logic Đơn Giản (Không cần Database)**

### **Chạy script test logic:**

```bash
cd backend
python test_vector_logic_simple.py
```

### **Kết quả mong đợi:**

```
🔍 **Kiểm Tra Logic Vector Đơn Giản**
============================================================
📋 **Vector Feature Names:**
  • Total features: 30
  • Location features (5): ['location_north_america', 'location_europe', 'location_asia', 'location_southeast_asia', 'location_other']

🧪 **Test Location Encoding Với Dữ Liệu Thực Tế:**
📍 **Test: Vietnamese User 1**
   Input: 'Ho Chi Minh City, Vietnam, 70000'
   Location Vector: [0.0, 0.0, 0.0, 1.0, 0.0]
   Active Region: southeast_asia
   ✅ Vietnamese user được encode ĐÚNG vào southeast_asia

🇻🇳 **Vietnamese Users Check:**
  • Total Vietnamese users: 4
  • Correctly encoded: 4
  • Accuracy: 100.0%
  ✅ TẤT CẢ Vietnamese users được encode ĐÚNG!

🔢 **Vector Structure Check:**
  ✅ Vector structure ĐÚNG (30 features, có southeast_asia)
```

## 🗄️ **Phương Pháp 2: Kiểm Tra Với Database Thực Tế**

### **Bước 1: Mở Django Shell**

```bash
cd backend
python manage.py shell
```

### **Bước 2: Chạy code kiểm tra**

```python
# Import các module cần thiết
from apps.users.models import User
from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

# Khởi tạo vectorizer
vectorizer = AdvancedDemographicVectorizer()
similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

# Kiểm tra vector features
feature_names = vectorizer.get_feature_names()
print(f"Total features: {len(feature_names)}")
location_features = [f for f in feature_names if f.startswith('location_')]
print(f"Location features: {location_features}")

# Lấy users từ database
users = User.objects.all()
print(f"Total users: {users.count()}")

# Kiểm tra Vietnamese users
vietnamese_users = users.filter(location__icontains='Vietnam')
print(f"Vietnamese users: {vietnamese_users.count()}")

# Test với user đầu tiên có location data
user_with_location = users.exclude(location__isnull=True).exclude(location='').first()
if user_with_location:
    print(f"\nTesting user: {user_with_location.username}")
    print(f"Location: {user_with_location.location}")

    # Tạo vector
    user_vector = vectorizer.vectorize_user(user_with_location)
    print(f"Vector length: {len(user_vector)}")

    # Phân tích location vector
    location_vector = user_vector[17:22]  # Location features
    region_names = list(vectorizer.location_regions.keys())

    active_region = None
    for i, val in enumerate(location_vector):
        if val == 1.0:
            active_region = region_names[i]
            break

    print(f"Location vector: {location_vector}")
    print(f"Active region: {active_region}")

    # Kiểm tra Vietnamese user
    if 'Vietnam' in user_with_location.location or 'Việt' in user_with_location.location:
        if active_region == 'southeast_asia':
            print("✅ Vietnamese user được encode ĐÚNG!")
        else:
            print(f"❌ Vietnamese user bị encode SAI vào {active_region}")
```

## 🔍 **Phương Pháp 3: Kiểm Tra Chi Tiết Vector**

### **Kiểm tra từng phần của vector:**

```python
# Tạo vector cho user
user_vector = vectorizer.vectorize_user(user)

# Phân tích từng phần
age_vector = user_vector[:6]           # 6 features
gender_vector = user_vector[6:9]       # 3 features
occupation_vector = user_vector[9:17]  # 8 features
location_vector = user_vector[17:22]   # 5 features (QUAN TRỌNG)
user_type_vector = user_vector[22:26]  # 4 features
behavioral_vector = user_vector[26:30] # 4 features

print(f"Age vector: {age_vector}")
print(f"Gender vector: {gender_vector}")
print(f"Occupation vector: {occupation_vector}")
print(f"Location vector: {location_vector}")  # Kiểm tra kỹ phần này
print(f"User type vector: {user_type_vector}")
print(f"Behavioral vector: {behavioral_vector}")
```

## 🎯 **Các Điểm Cần Kiểm Tra**

### **1. Vector Structure:**

- ✅ Total features: 30 (tăng từ 29)
- ✅ Location features: 5 (bao gồm southeast_asia)
- ✅ Southeast Asia feature: `location_southeast_asia`

### **2. Location Encoding:**

- ✅ Vietnamese users → `southeast_asia`
- ✅ Thai users → `southeast_asia`
- ✅ Singapore users → `southeast_asia`
- ✅ US users → `north_america`
- ✅ UK users → `europe`
- ✅ Japanese users → `asia`

### **3. Vector Indices:**

```python
# Location vector indices (17-22)
location_vector = user_vector[17:22]
# [0] = north_america
# [1] = europe
# [2] = asia
# [3] = southeast_asia  # QUAN TRỌNG
# [4] = other
```

## 🚨 **Các Vấn Đề Cần Chú Ý**

### **1. Nếu Vietnamese users bị encode sai:**

```python
# Debug location encoding
test_vector = vectorizer._encode_location(user.location, user.zip_code)
print(f"Expected: {test_vector}")
print(f"Actual: {location_vector}")
```

### **2. Nếu vector length không đúng:**

```python
# Kiểm tra feature names
feature_names = vectorizer.get_feature_names()
print(f"Feature count: {len(feature_names)}")
print(f"Features: {feature_names}")
```

### **3. Nếu location features thiếu:**

```python
# Kiểm tra location_regions
print(f"Location regions: {vectorizer.location_regions}")
print(f"Southeast Asia countries: {vectorizer.location_regions['southeast_asia']}")
```

## 📊 **Kết Quả Mong Đợi**

### **✅ Khi hệ thống hoạt động đúng:**

```
🔢 **Vector Structure Check:**
  • Total features: 30
  • Location features: 5
  • Southeast Asia feature: True
  ✅ Vector structure ĐÚNG (30 features, có southeast_asia)

🇻🇳 **Vietnamese Users Check:**
  • Total Vietnamese users: 4
  • Correctly encoded: 4
  • Accuracy: 100.0%
  ✅ TẤT CẢ Vietnamese users được encode ĐÚNG!

🎯 **Kết luận:**
  • Vector đã được cập nhật từ 29 → 30 features
  • Southeast Asia region đã được thêm
  • Vietnamese users được encode đúng vào southeast_asia
  • Hệ thống demographic filtering đã sẵn sàng!
```

### **❌ Khi có vấn đề:**

- Vector length ≠ 30
- Location features thiếu `southeast_asia`
- Vietnamese users bị encode vào `europe` hoặc `asia`
- Location encoding không khớp với expected

## 🔧 **Cách Sửa Lỗi**

### **1. Nếu vector length sai:**

- Kiểm tra `get_feature_names()` method
- Đảm bảo tất cả 6 feature groups được tính đúng

### **2. Nếu location encoding sai:**

- Kiểm tra `location_regions` dictionary
- Kiểm tra `country_mapping` dictionary
- Kiểm tra logic `_encode_location()` method

### **3. Nếu Vietnamese users bị encode sai:**

- Đảm bảo `'VN'` có trong `southeast_asia` region
- Đảm bảo `'Vietnam'` và `'Việt Nam'` được map thành `'VN'`
- Kiểm tra word-based matching logic

## 📝 **Ghi Chú**

- **Vector indices**: Location features bắt đầu từ index 17
- **Southeast Asia index**: 3 trong location vector (index 20 trong toàn bộ vector)
- **Country mapping**: Hỗ trợ cả tiếng Anh và tiếng Việt
- **Word-based matching**: Sử dụng regex để tránh false positives

**Hệ thống demographic filtering đã được cập nhật và sẵn sàng để sử dụng!** 🎉
