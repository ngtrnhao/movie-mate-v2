# Sửa Field Name Mismatch - Email Verification

## 🔍 **Vấn đề đã xác định**

Từ debug logs, tôi đã tìm ra **nguyên nhân chính**:

### **Field Name Mismatch**

- **Backend trả về**: `"is_email_verified": true` (snake_case)
- **Frontend access**: `user?.isEmailVerified` (camelCase)
- **Kết quả**: `userEmailVerified: undefined`

### **Debug Logs phân tích**

```
userEmailVerified: undefined  // ❌ VẤN ĐỀ: Undefined
userEmailVerifiedType: "undefined"  // ❌ VẤN ĐỀ: Type undefined
userKeys: ['id', 'username', 'email', ..., 'is_email_verified', ...]  // ✅ Field tồn tại
userStringified: "{\"is_email_verified\":true,...}"  // ✅ Data có đúng
```

## 🔧 **Giải pháp đã áp dụng**

### 1. **Support cả hai field names**

```javascript
// Trước:
const shouldShow = !!(
  state.isAuthenticated &&
  user?.isEmailVerified && // ❌ Chỉ support camelCase
  !user?.is_profile_complete &&
  user?.profile_completion_percentage < 80
);

// Sau:
const shouldShow = !!(
  state.isAuthenticated &&
  (user?.isEmailVerified || user?.is_email_verified) && // ✅ Support cả hai
  !user?.is_profile_complete &&
  user?.profile_completion_percentage < 80
);
```

### 2. **Thêm debug logging cho snake_case**

```javascript
console.log("🔍 checkAndShowProfileModal - Current state:", {
  isAuthenticated: state.isAuthenticated,
  userEmailVerified: user?.isEmailVerified, // camelCase
  userEmailVerifiedSnake: user?.is_email_verified, // snake_case
  userProfileComplete: user?.is_profile_complete,
  userCompletionPercentage: user?.profile_completion_percentage,
  userExists: !!user,
  userKeys: user ? Object.keys(user) : "No user",
  userEmailVerifiedType: typeof user?.isEmailVerified,
  userEmailVerifiedValue: user?.isEmailVerified,
  userStringified: user ? JSON.stringify(user) : "No user",
});
```

### 3. **Thêm debug cho login**

```javascript
console.log("🔍 login.fulfilled - User data received:", {
  user: action.payload.user,
  isEmailVerified: action.payload.user?.isEmailVerified, // camelCase
  isEmailVerifiedSnake: action.payload.user?.is_email_verified, // snake_case
  isProfileComplete: action.payload.user?.is_profile_complete,
  profileCompletionPercentage:
    action.payload.user?.profile_completion_percentage,
});
```

## 🎯 **Kết quả mong đợi**

Sau khi fix, modal sẽ hiện khi:

1. ✅ User authenticated
2. ✅ Email verified (`user?.is_email_verified = true`)
3. ✅ Profile incomplete (`user?.is_profile_complete = false`)
4. ✅ Completion < 80% (`user?.profile_completion_percentage = 0`)

## 📋 **Test Cases**

### **Test Case 1: User với đủ điều kiện**

```
User: kokibejo@forexzig.com
is_email_verified: true ✅
is_profile_complete: false ✅
profile_completion_percentage: 0 ✅
Expected: Modal should show ✅
```

### **Test Case 2: User với email chưa verify**

```
User: [any user]
is_email_verified: false ❌
Expected: Modal should not show ✅
```

### **Test Case 3: User với profile complete**

```
User: [any user]
is_profile_complete: true ❌
Expected: Modal should not show ✅
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

Vấn đề chính là **field name mismatch** giữa backend (snake_case) và frontend (camelCase). Giải pháp là support cả hai field names để đảm bảo modal hiện đúng khi user có đủ điều kiện.
