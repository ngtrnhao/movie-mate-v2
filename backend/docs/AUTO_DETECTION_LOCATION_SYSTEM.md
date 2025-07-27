# 🗺️ Auto Detection Location System

## 📋 **Tổng quan**

**Auto Detection Location** là một hệ thống thông minh tự động phát hiện và cập nhật vị trí địa lý của người dùng trong hệ thống Movie Recommendation. Hệ thống này sử dụng nhiều phương pháp khác nhau để đảm bảo độ chính xác và tính khả dụng cao.

## 🎯 **Mục đích**

### **1. Cải thiện trải nghiệm người dùng**

- Tự động điền thông tin vị trí cho người dùng mới
- Giảm thiểu việc nhập liệu thủ công
- Tăng tốc độ hoàn thành profile

### **2. Tối ưu hóa hệ thống recommendation**

- Cung cấp dữ liệu demographic chính xác
- Cải thiện độ chính xác của thuật toán filtering
- Phân tích xu hướng theo khu vực địa lý

### **3. Phân tích và thống kê**

- Thống kê người dùng theo khu vực
- Phân tích xu hướng nội dung theo địa lý
- Báo cáo marketing theo vùng miền

## 🏗️ **Kiến trúc hệ thống**

### **Backend Architecture:**

```
LocationDetectionView
├── _get_client_ip()          # Lấy IP từ request
├── _get_location_from_ip()   # Geocoding từ IP
└── _get_location_from_coordinates() # Reverse geocoding
```

### **Frontend Architecture:**

```
autoDetectLocationAPI()
├── Browser Geolocation API   # Lấy tọa độ từ browser
├── detectLocationAPI()       # Gửi tọa độ lên backend
└── Fallback to IP detection  # Fallback nếu geolocation thất bại
```

## 🔧 **Các phương pháp phát hiện vị trí**

### **1. Browser Geolocation API (Ưu tiên cao nhất)**

#### **Cách hoạt động:**

```javascript
navigator.geolocation.getCurrentPosition(
  async (position) => {
    const { latitude, longitude } = position.coords;
    const result = await detectLocationAPI({ latitude, longitude });
  },
  (error) => {
    // Fallback to IP-based detection
  },
  {
    timeout: 10000,
    enableHighAccuracy: false,
  }
);
```

#### **Ưu điểm:**

- ✅ Độ chính xác cao (GPS/WiFi triangulation)
- ✅ Hoạt động trên mobile devices
- ✅ Real-time location data

#### **Nhược điểm:**

- ❌ Cần permission từ user
- ❌ Không hoạt động trên một số browser cũ
- ❌ Có thể bị chặn bởi privacy settings

### **2. IP-based Geolocation (Fallback)**

#### **Cách hoạt động:**

```python
def _get_location_from_ip(self, ip_address):
    """Get location data from IP address using ip-api.com"""
    try:
        # Skip local/private IPs
        if ip_address in ['127.0.0.1', '::1'] or ip_address.startswith('192.168.'):
            return None

        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country'),
                    'region': data.get('regionName'),
                    'city': data.get('city'),
                    'zip_code': data.get('zip'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                }
    except Exception as e:
        logger.error(f"Error getting location from IP {ip_address}: {str(e)}")

    return None
```

#### **Ưu điểm:**

- ✅ Hoạt động trên mọi thiết bị
- ✅ Không cần permission
- ✅ Fallback reliable

#### **Nhược điểm:**

- ❌ Độ chính xác thấp hơn (city/region level)
- ❌ Có thể bị ảnh hưởng bởi VPN/Proxy
- ❌ Phụ thuộc vào third-party service

### **3. Reverse Geocoding (Từ tọa độ)**

#### **Cách hoạt động:**

```python
def _get_location_from_coordinates(self, latitude, longitude):
    """Get location data from coordinates using OpenStreetMap Nominatim"""
    try:
        url = f'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
        }

        headers = {
            'User-Agent': 'MovieMate/1.0'  # Required by Nominatim
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})

            return {
                'country': address.get('country'),
                'region': address.get('state') or address.get('region'),
                'city': address.get('city') or address.get('town'),
                'zip_code': address.get('postcode'),
                'latitude': latitude,
                'longitude': longitude,
            }
    except Exception as e:
        logger.error(f"Error getting location from coordinates: {str(e)}")

    return None
```

#### **Ưu điểm:**

- ✅ Độ chính xác cao
- ✅ Free service (OpenStreetMap)
- ✅ Không cần API key

#### **Nhược điểm:**

- ❌ Cần tọa độ chính xác
- ❌ Rate limiting từ service
- ❌ Phụ thuộc vào third-party service

## 🔄 **Flow hoạt động**

### **1. Frontend Flow:**

```
User clicks "Auto Detect Location"
    ↓
Check if browser supports geolocation
    ↓
Request geolocation permission
    ↓
Get coordinates from browser
    ↓
Send coordinates to backend API
    ↓
Backend processes coordinates
    ↓
Update user location in database
    ↓
Return location data to frontend
    ↓
Update UI with detected location
```

### **2. Backend Flow:**

```
Receive location request
    ↓
Validate input data
    ↓
Check detection method priority:
    1. Coordinates (if provided)
    2. IP address (if provided)
    3. Client IP (automatic)
    ↓
Call appropriate geocoding service
    ↓
Process and validate location data
    ↓
Update user profile
    ↓
Return success response
```

### **3. Fallback Strategy:**

```
Primary: Browser Geolocation
    ↓ (if fails)
Secondary: IP-based detection
    ↓ (if fails)
Tertiary: Manual input required
```

## 📊 **Data Structure**

### **Location Data Format:**

```json
{
  "country": "Vietnam",
  "region": "Ho Chi Minh",
  "city": "Ho Chi Minh City",
  "zip_code": "70000",
  "latitude": 10.8231,
  "longitude": 106.6297
}
```

### **API Response Format:**

```json
{
  "status": "success",
  "message": "Location detected and updated successfully",
  "data": {
    "location": "Ho Chi Minh City, Vietnam",
    "zip_code": "70000",
    "detected_data": {
      "country": "Vietnam",
      "region": "Ho Chi Minh",
      "city": "Ho Chi Minh City",
      "zip_code": "70000",
      "latitude": 10.8231,
      "longitude": 106.6297
    }
  }
}
```

## 🛡️ **Bảo mật và Privacy**

### **1. Data Protection:**

- ✅ Chỉ lưu trữ thông tin cần thiết
- ✅ Không lưu trữ tọa độ chính xác
- ✅ Tuân thủ GDPR/CCPA

### **2. Permission Handling:**

- ✅ Yêu cầu permission rõ ràng
- ✅ Fallback graceful khi bị từ chối
- ✅ Không force user cung cấp location

### **3. Error Handling:**

- ✅ Timeout protection (10 seconds)
- ✅ Network error handling
- ✅ Graceful degradation

## 🔧 **Implementation Details**

### **1. Backend Implementation:**

#### **LocationDetectionView:**

```python
class LocationDetectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Detect location from IP or coordinates"""
        serializer = LocationDetectionSerializer(data=request.data)

        if serializer.is_valid():
            location_data = serializer.validated_data
            detected_location = None

            # Method 1: Use provided coordinates
            if 'latitude' in location_data and 'longitude' in location_data:
                detected_location = self._get_location_from_coordinates(
                    location_data['latitude'],
                    location_data['longitude']
                )

            # Method 2: Use IP address
            elif 'ip_address' in location_data:
                detected_location = self._get_location_from_ip(location_data['ip_address'])

            # Method 3: Use client IP
            else:
                client_ip = self._get_client_ip(request)
                if client_ip:
                    detected_location = self._get_location_from_ip(client_ip)

            if detected_location:
                # Update user location
                user = request.user
                if detected_location.get('city') and detected_location.get('country'):
                    location_string = f"{detected_location['city']}, {detected_location['country']}"
                    user.location = location_string

                if detected_location.get('zip_code'):
                    user.zip_code = detected_location['zip_code']

                user.save()

                return Response({
                    'status': 'success',
                    'message': 'Location detected and updated successfully',
                    'data': {
                        'location': user.location,
                        'zip_code': user.zip_code,
                        'detected_data': detected_location
                    }
                })
```

### **2. Frontend Implementation:**

#### **Auto Detection Function:**

```javascript
export const autoDetectLocationAPI = async () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject({ error: "Geolocation is not supported by this browser" });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const result = await detectLocationAPI({ latitude, longitude });
          resolve(result);
        } catch (error) {
          reject(error);
        }
      },
      (error) => {
        // Fallback to IP-based detection if geolocation fails
        detectLocationAPI().then(resolve).catch(reject);
      },
      {
        timeout: 10000,
        enableHighAccuracy: false,
      }
    );
  });
};
```

#### **UI Integration:**

```javascript
const handleAutoDetectLocation = async () => {
  setLoadingLocation(true);
  try {
    const result = await autoDetectLocationAPI();

    if (result.status === "success") {
      setFormData((prev) => ({
        ...prev,
        location: result.data.location || prev.location,
        zip_code: result.data.zip_code || prev.zip_code,
      }));
      toast.success("Location detected successfully!");
    }
  } catch (error) {
    console.error("Error detecting location:", error);
    toast.error("Could not detect location automatically");
  } finally {
    setLoadingLocation(false);
  }
};
```

## 📈 **Performance Optimization**

### **1. Caching Strategy:**

- ✅ Cache location data trong session
- ✅ Avoid repeated API calls
- ✅ Store location preferences

### **2. Rate Limiting:**

- ✅ Respect API rate limits
- ✅ Implement exponential backoff
- ✅ Use multiple geocoding services

### **3. Error Recovery:**

- ✅ Automatic retry mechanism
- ✅ Fallback service switching
- ✅ Graceful degradation

## 🧪 **Testing Strategy**

### **1. Unit Tests:**

```python
def test_get_location_from_ip(self):
    """Test IP-based location detection"""
    view = LocationDetectionView()
    result = view._get_location_from_ip('8.8.8.8')
    self.assertIsNotNone(result)
    self.assertIn('country', result)

def test_get_location_from_coordinates(self):
    """Test coordinate-based location detection"""
    view = LocationDetectionView()
    result = view._get_location_from_coordinates(10.8231, 106.6297)
    self.assertIsNotNone(result)
    self.assertEqual(result['city'], 'Ho Chi Minh City')
```

### **2. Integration Tests:**

```python
def test_location_detection_api(self):
    """Test complete location detection flow"""
    response = self.client.post('/api/auth/profile/detect-location/', {
        'latitude': 10.8231,
        'longitude': 106.6297
    })
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['status'], 'success')
```

### **3. Frontend Tests:**

```javascript
test("autoDetectLocationAPI should detect location successfully", async () => {
  // Mock geolocation API
  const mockPosition = {
    coords: { latitude: 10.8231, longitude: 106.6297 },
  };

  global.navigator.geolocation = {
    getCurrentPosition: jest
      .fn()
      .mockImplementation((success) => success(mockPosition)),
  };

  const result = await autoDetectLocationAPI();
  expect(result.status).toBe("success");
});
```

## 🚀 **Deployment Considerations**

### **1. Environment Variables:**

```bash
# Geocoding service configuration
GEOCODING_SERVICE_URL=https://nominatim.openstreetmap.org
IP_GEOCODING_SERVICE_URL=http://ip-api.com
GEOCODING_TIMEOUT=5
GEOCODING_USER_AGENT=MovieMate/1.0
```

### **2. Service Dependencies:**

- ✅ OpenStreetMap Nominatim (free)
- ✅ ip-api.com (free tier)
- ✅ Fallback services ready

### **3. Monitoring:**

- ✅ API response times
- ✅ Success/failure rates
- ✅ Error tracking
- ✅ Usage analytics

## 📊 **Analytics và Metrics**

### **1. Success Metrics:**

- Location detection success rate
- Average detection time
- User adoption rate
- Accuracy improvement

### **2. Performance Metrics:**

- API response time
- Cache hit rate
- Error rate by method
- Service availability

### **3. Business Metrics:**

- Profile completion rate improvement
- User engagement increase
- Recommendation accuracy
- Geographic user distribution

## 🔮 **Future Enhancements**

### **1. Advanced Features:**

- Real-time location tracking
- Location-based notifications
- Geographic content filtering
- Regional trend analysis

### **2. Machine Learning Integration:**

- Location prediction models
- User behavior analysis
- Geographic preference learning
- Dynamic location weighting

### **3. Privacy Enhancements:**

- Local location processing
- Differential privacy
- User consent management
- Data anonymization

## 🎯 **Kết luận**

Hệ thống **Auto Detection Location** cung cấp một giải pháp toàn diện và thông minh để tự động phát hiện vị trí người dùng. Với nhiều phương pháp phát hiện và fallback strategy, hệ thống đảm bảo độ tin cậy cao và trải nghiệm người dùng tốt nhất.

### **Key Benefits:**

- ✅ **User Experience**: Tự động điền thông tin, giảm friction
- ✅ **Accuracy**: Multiple detection methods, high precision
- ✅ **Reliability**: Fallback strategies, error handling
- ✅ **Privacy**: Respect user consent, data protection
- ✅ **Performance**: Caching, optimization, monitoring
- ✅ **Scalability**: Cloud-ready, service-oriented architecture
