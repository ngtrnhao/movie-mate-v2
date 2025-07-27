# Sửa Profile Modal Conflict - App.jsx vs authSlice.js

## 🔍 **Vấn đề đã xác định**

Có **conflict giữa hai logic khác nhau**:

### **1. App.jsx (Custom Hook)**

```
Profile Completion Modal Conditions: {
  isAuthenticated: true,
  isEmailVerified: false,  // ❌ False (sử dụng camelCase)
  isProfileComplete: false,
  profileCompletionPercentage: 0,
  shouldShowModal: false  // ❌ False
}
```

### **2. authSlice.js (Redux State)**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: undefined,  // ❌ Undefined (camelCase không tồn tại)
  userEmailVerifiedSnake: true,  // ✅ True (snake_case có data)
  userProfileComplete: undefined,
  userCompletionPercentage: undefined,
  shouldShowModal: false  // ❌ False
}
```

### **3. User Object Analysis**

```
userKeys: [
  'id', 'username', 'email', 'firstName', 'lastName', 'avatarUrl', 'bio',
  'birth_date', 'age', 'age_group', 'gender', 'occupation', 'location',
  'zip_code', 'isEmailVerified', 'createdAt', 'updatedAt', 'user_type',
  'groups', 'is_profile_complete', 'profile_completion_percentage',
  'first_name', 'last_name', 'avatar_url', 'is_email_verified',  // ✅ Có snake_case
  'created_at', 'updated_at', 'occupation_display', 'gender_display',
  'age_group_display'
]
```

## 🔧 **Nguyên nhân**

### **Field Name Inconsistency**

- **Backend trả về**: `is_email_verified` (snake_case)
- **Frontend access**: `isEmailVerified` (camelCase)
- **Kết quả**: `undefined` cho camelCase field

### **Logic Conflict**

1. **Custom Hook**: Sử dụng `user.isEmailVerified` → `undefined` → `false`
2. **Redux Slice**: Sử dụng `user?.is_email_verified` → `true`
3. **Kết quả**: Modal bị tắt ngay lập tức

## 🔧 **Giải pháp đã áp dụng**

### **1. Sửa Custom Hook (`useProfileCompletionModal.js`)**

```javascript
// Trước:
return (
  user.isEmailVerified &&
  !user.is_profile_complete &&
  user.profile_completion_percentage < 80
);

// Sau:
return (
  (user.isEmailVerified || user.is_email_verified) && // ✅ Support cả hai
  !user.is_profile_complete &&
  user.profile_completion_percentage < 80
);
```

### **2. Cập nhật useEffect Dependencies**

```javascript
useEffect(() => {
  if (isAuthenticated && user) {
    checkModalVisibility();
  }
}, [
  isAuthenticated,
  user?.isEmailVerified, // camelCase
  user?.is_email_verified, // snake_case (thêm)
  user?.is_profile_complete,
  user?.profile_completion_percentage,
]);
```

### **3. Redux Slice đã được sửa trước đó**

```javascript
const shouldShow = !!(
  state.isAuthenticated &&
  (user?.isEmailVerified || user?.is_email_verified) && // ✅ Support cả hai
  !user?.is_profile_complete &&
  user?.profile_completion_percentage < 80
);
```

## 🎯 **Kết quả mong đợi**

Sau khi fix, cả hai logic sẽ đồng bộ:

### **Expected State**

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
- **Frontend**: Nên sử dụng camelCase (`isEmailVerified`)
- **Giải pháp**: Support cả hai để đảm bảo compatibility

### **Future Improvements**

1. **Standardize field names**: Đồng bộ field names giữa backend và frontend
2. **Add field mapping**: Tạo mapping function để convert field names
3. **Update serializers**: Cập nhật serializers để trả về camelCase

## 🎯 **Kết luận**

Vấn đề chính là **field name inconsistency** giữa backend (snake_case) và frontend (camelCase) dẫn đến **logic conflict** giữa custom hook và Redux slice. Giải pháp là support cả hai field names để đảm bảo modal hiện đúng khi user có đủ điều kiện.
