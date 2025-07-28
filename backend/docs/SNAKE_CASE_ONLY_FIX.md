# Sử dụng Snake Case Only - is_email_verified

## 🔍 **Vấn đề đã xác định**

Mặc dù đã sửa hardcoded fields, nhưng **logic vẫn đang access camelCase field** không tồn tại:

### **1. User Object Analysis**

```
userKeys: [
  'id', 'username', 'email', 'firstName', 'lastName', 'avatarUrl', 'bio',
  'birth_date', 'age', 'age_group', 'gender', 'occupation', 'location',
  'zip_code', 'createdAt', 'updatedAt', 'user_type', 'groups',
  'is_profile_complete', 'profile_completion_percentage', 'first_name',
  'last_name', 'avatar_url', 'is_email_verified',  // ✅ Chỉ có snake_case
  'created_at', 'updated_at', 'occupation_display', 'gender_display',
  'age_group_display'
]
```

### **2. Field Access Issue**

```
userEmailVerified: undefined,  // ❌ Access camelCase không tồn tại
userEmailVerifiedSnake: true,  // ✅ Access snake_case có data
```

### **3. Debug Logs**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: undefined,      // ❌ Undefined (camelCase không tồn tại)
  userEmailVerifiedSnake: true,      // ✅ True (snake_case có data)
  userProfileComplete: false,
  userCompletionPercentage: 0,
  shouldShowModal: false  // ❌ False (do undefined field)
}
```

## 🔧 **Nguyên nhân**

### **Logic vẫn access camelCase**

1. **authSlice.js**: `user?.isEmailVerified` → `undefined`
2. **custom hook**: `user.isEmailVerified` → `undefined`
3. **Kết quả**: Modal không hiện do undefined field

### **Field Name Inconsistency**

- **Backend trả về**: `is_email_verified` (snake_case)
- **Frontend access**: `isEmailVerified` (camelCase)
- **Kết quả**: Field không tồn tại

## 🔧 **Giải pháp đã áp dụng**

### **1. Sửa authSlice.js**

```javascript
// Trước:
userEmailVerified: user?.isEmailVerified,  // ❌ camelCase
userEmailVerifiedSnake: user?.is_email_verified,  // snake_case

// Sau:
userEmailVerified: user?.is_email_verified,  // ✅ snake_case only
```

### **2. Sửa shouldShow logic**

```javascript
// Trước:
const shouldShow = !!(
  state.isAuthenticated &&
  (user?.isEmailVerified || user?.is_email_verified) && // ❌ Support cả hai
  !user?.is_profile_complete &&
  user?.profile_completion_percentage < 80
);

// Sau:
const shouldShow = !!(
  state.isAuthenticated &&
  user?.is_email_verified && // ✅ snake_case only
  !user?.is_profile_complete &&
  user?.profile_completion_percentage < 80
);
```

### **3. Sửa custom hook**

```javascript
// Trước:
return (
  (user.isEmailVerified || user.is_email_verified) && // ❌ Support cả hai
  !user.is_profile_complete &&
  user.profile_completion_percentage < 80
);

// Sau:
return (
  user.is_email_verified && // ✅ snake_case only
  !user.is_profile_complete &&
  user.profile_completion_percentage < 80
);
```

### **4. Sửa useEffect dependencies**

```javascript
// Trước:
useEffect(() => {
  // ...
}, [
  isAuthenticated,
  user?.isEmailVerified, // ❌ camelCase
  user?.is_email_verified, // snake_case
  user?.is_profile_complete,
  user?.profile_completion_percentage,
]);

// Sau:
useEffect(() => {
  // ...
}, [
  isAuthenticated,
  user?.is_email_verified, // ✅ snake_case only
  user?.is_profile_complete,
  user?.profile_completion_percentage,
]);
```

## 🎯 **Kết quả mong đợi**

Sau khi fix, logic sẽ chỉ sử dụng snake_case:

### **Expected Debug Logs**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: true,      // ✅ True (snake_case)
  userProfileComplete: false,
  userCompletionPercentage: 0,
  shouldShowModal: true  // ✅ True (do snake_case field)
}
```

### **Expected Modal Behavior**

```
App.jsx: shouldShowModal: true  ✅
authSlice.js: showProfileCompletionModal: true  ✅
Modal: Hiển thị  ✅
```

### **User Data**

```
User: kokibejo@forexzig.com
is_email_verified: true ✅
is_profile_complete: false ✅
profile_completion_percentage: 0 ✅
Expected: Modal should show ✅
```

## 🚨 **Lưu ý quan trọng**

### **Field Name Convention**

- **Backend**: Sử dụng snake_case (`is_email_verified`)
- **Frontend**: Chỉ sử dụng snake_case (`is_email_verified`)
- **Giải pháp**: Đồng bộ field names

### **Future Improvements**

1. **Standardize field names**: Đồng bộ field names giữa backend và frontend
2. **Add field mapping**: Tạo mapping function để convert field names
3. **Update serializers**: Cập nhật serializers để trả về camelCase

## 🎯 **Kết luận**

Vấn đề chính là **logic vẫn đang access camelCase field** không tồn tại trong user object. Giải pháp là **chỉ sử dụng snake_case field** để đảm bảo consistency với backend data.
