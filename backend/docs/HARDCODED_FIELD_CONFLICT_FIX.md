# Sửa Hardcoded Field Conflict - isEmailVerified

## 🔍 **Vấn đề đã xác định**

Có **conflict giữa hardcoded fields và backend data**:

### **1. User Object Analysis**

```
userKeys: [
  'id', 'username', 'email', 'firstName', 'lastName', 'avatarUrl', 'bio',
  'birth_date', 'age', 'age_group', 'gender', 'occupation', 'location',
  'zip_code', 'isEmailVerified', 'createdAt', 'updatedAt', 'user_type',
  'groups', 'is_profile_complete', 'profile_completion_percentage',
  'first_name', 'last_name', 'avatar_url', 'is_email_verified',  // ✅ Backend data
  'created_at', 'updated_at', 'occupation_display', 'gender_display',
  'age_group_display'
]
```

### **2. Field Values Conflict**

```
isEmailVerified: false,      // ❌ Hardcoded false (camelCase)
is_email_verified: true,     // ✅ Backend data true (snake_case)
```

### **3. Debug Logs**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: false,      // ❌ False (hardcoded)
  userEmailVerifiedSnake: true,  // ✅ True (backend)
  userProfileComplete: false,
  userCompletionPercentage: 0,
  shouldShowModal: false  // ❌ False (do hardcoded field)
}
```

## 🔧 **Nguyên nhân**

### **Hardcoded Fields trong Redux**

1. **initialState**: `isEmailVerified: false`
2. **register thunk**: `isEmailVerified: false`
3. **logout reducer**: `isEmailVerified: false`

### **Field Mapping Conflict**

- **Backend trả về**: `is_email_verified: true`
- **Frontend hardcode**: `isEmailVerified: false`
- **Kết quả**: User object có cả hai field với giá trị khác nhau

## 🔧 **Giải pháp đã áp dụng**

### **1. Sửa initialState**

```javascript
// Trước:
user: {
  // ...
  isEmailVerified: false,  // ❌ Hardcoded false
  // ...
}

// Sau:
user: {
  // ...
  // Remove hardcoded isEmailVerified to use backend data  // ✅
  // ...
}
```

### **2. Sửa register thunk**

```javascript
// Trước:
user: {
  ...response.user,
  isEmailVerified: false,  // ❌ Hardcoded false
  // ...
}

// Sau:
user: {
  ...response.user,
  // Remove hardcoded isEmailVerified to use backend data  // ✅
  // ...
}
```

### **3. Sửa logout reducer**

```javascript
// Trước:
state.user = {
  // ...
  isEmailVerified: false, // ❌ Hardcoded false
  // ...
};

// Sau:
state.user = {
  // ...
  // Remove hardcoded isEmailVerified to use backend data  // ✅
  // ...
};
```

## 🎯 **Kết quả mong đợi**

Sau khi fix, user object sẽ chỉ có backend data:

### **Expected User Object**

```
{
  // ... other fields
  is_email_verified: true,  // ✅ Chỉ có backend data
  // Không có isEmailVerified hardcoded
}
```

### **Expected Debug Logs**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: undefined,      // ✅ Undefined (không có hardcoded)
  userEmailVerifiedSnake: true,      // ✅ True (backend data)
  userProfileComplete: false,
  userCompletionPercentage: 0,
  shouldShowModal: true  // ✅ True (do backend data)
}
```

### **Expected Modal Behavior**

```
App.jsx: shouldShowModal: true  ✅
authSlice.js: showProfileCompletionModal: true  ✅
Modal: Hiển thị  ✅
```

## 🚨 **Lưu ý quan trọng**

### **Field Name Convention**

- **Backend**: Sử dụng snake_case (`is_email_verified`)
- **Frontend**: Không hardcode field names
- **Giải pháp**: Chỉ sử dụng backend data

### **Future Improvements**

1. **Standardize field names**: Đồng bộ field names giữa backend và frontend
2. **Add field mapping**: Tạo mapping function để convert field names
3. **Update serializers**: Cập nhật serializers để trả về camelCase

## 🎯 **Kết luận**

Vấn đề chính là **hardcoded field values** trong Redux state tạo ra **conflict** với backend data. Giải pháp là loại bỏ tất cả hardcoded fields và chỉ sử dụng backend data để đảm bảo consistency.
