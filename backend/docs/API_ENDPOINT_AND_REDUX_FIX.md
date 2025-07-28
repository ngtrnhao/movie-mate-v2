# Sửa API Endpoint và Redux Action - Profile Completion

## 🔍 **Vấn đề đã xác định**

### **1. API Endpoint Sai**

```
WARNING 2025-07-27 07:25:00,546 log 987 140010218497728 Not Found: /api/auth/profile/
```

**Frontend gọi**: `PUT /api/auth/profile/`
**Backend có**: `PATCH /api/auth/profile/update/`

### **2. Redux Action Sai**

```
userProfileComplete: false ❌
userCompletionPercentage: 0 ❌
```

**Frontend gọi**: `updateProfile` (async thunk)
**Cần gọi**: `updateProfileCompletion` (reducer)

## 🔧 **Giải pháp đã áp dụng**

### **1. Sửa API Endpoint trong auth.js**

```javascript
// Trước
export const updateProfileAPI = async (userData) => {
  const response = await axiosInstance.put("/api/auth/profile/", userData);
  return response.data;
};

// Sau
export const updateProfileAPI = async (userData) => {
  const response = await axiosInstance.patch(
    "/api/auth/profile/update/",
    userData
  );
  return response.data;
};
```

### **2. Sửa Redux Action trong ProfileCompletionModal.jsx**

```javascript
// Trước
import { updateProfile } from "../../store/slices/authSlice";

dispatch(updateProfile(updatedUserData));

// Sau
import { updateProfileCompletion } from "../../store/slices/authSlice";

dispatch(
  updateProfileCompletion({
    is_profile_complete: statusData.data.is_complete,
    profile_completion_percentage: statusData.data.completion_percentage,
  })
);
```

### **3. Sửa cả 2 chỗ trong ProfileCompletionModal.jsx**

#### **Chỗ 1: loadInitialData**

```javascript
if (statusData.status === "success") {
  setCompletionStatus(statusData.data);

  // Update Redux state with fresh data from API
  dispatch(
    updateProfileCompletion({
      is_profile_complete: statusData.data.is_complete,
      profile_completion_percentage: statusData.data.completion_percentage,
    })
  );

  // Check if modal should still be shown
  if (
    statusData.data.is_complete ||
    statusData.data.completion_percentage >= 80
  ) {
    console.log("Profile is complete, closing modal...");
    onClose();
  }
}
```

#### **Chỗ 2: handleSubmit**

```javascript
if (result.status === "success") {
  // Update Redux store with new user data
  dispatch(
    updateProfileCompletion({
      is_profile_complete: result.data.is_profile_complete,
      profile_completion_percentage: result.data.profile_completion_percentage,
    })
  );

  toast.success("Profile completed successfully!");
  onClose();
}
```

## 🎯 **Kết quả mong đợi**

### **Expected API Calls**

```
✅ PATCH /api/auth/profile/update/ (thay vì PUT /api/auth/profile/)
✅ GET /api/auth/profile/completion-status/
```

### **Expected Redux State**

```
checkAndShowProfileModal - Current state: {
  isAuthenticated: true,
  userEmailVerified: true,      // ✅ Đúng
  userProfileComplete: true,    // ✅ Đúng (updated)
  userCompletionPercentage: 88, // ✅ Đúng (updated)
  shouldShowModal: false        // ✅ Đúng (không hiện modal)
}
```

### **Expected Modal Behavior**

```
Modal: Không hiện vì profile đã complete (88%) ✅
```

### **Expected Console Logs**

```
Loading initial data...
Status data: { is_complete: true, completion_percentage: 88 }
Profile is complete, closing modal...
```

## 🚨 **Lưu ý quan trọng**

### **API Endpoint Mapping**

- **Frontend**: `PATCH /api/auth/profile/update/`
- **Backend**: `ProfileUpdateView.as_view()`
- **Method**: `PATCH` (không phải `PUT`)

### **Redux Action Mapping**

- **updateProfileCompletion**: Reducer để update profile completion status
- **updateProfile**: Async thunk để update toàn bộ user data
- **Sử dụng**: `updateProfileCompletion` cho profile completion status

### **Data Flow**

```
API Response → Component → updateProfileCompletion → Redux State → Modal Logic
```

## 🎯 **Kết luận**

Vấn đề chính là **API endpoint sai** và **Redux action sai**. Giải pháp là:

1. **Sửa API endpoint**: `PUT /api/auth/profile/` → `PATCH /api/auth/profile/update/`
2. **Sửa Redux action**: `updateProfile` → `updateProfileCompletion`
3. **Auto-close modal**: Khi profile complete, modal tự động đóng
