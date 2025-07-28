# Sửa Modal Loading State - Tránh Flash Modal

## 🔍 **Vấn đề đã xác định**

### **Hiện tượng:**

Modal hiện rồi ẩn khi load trang hoặc F5 refresh:

```
1. Initial state: showProfileCompletionModal: false
2. Login/load: checkAndShowProfileModal được gọi
3. Modal hiện: showProfileCompletionModal: true
4. Data update: User data được cập nhật
5. Modal ẩn: showProfileCompletionModal: false
```

### **Nguyên nhân:**

- **State chưa được cập nhật kịp thời** khi load trang
- **checkAndShowProfileModal** được gọi trước khi profile data load xong
- **Modal logic** dựa trên data chưa đầy đủ

## 🔧 **Giải pháp đã áp dụng**

### **1. Thêm Profile Data Loading State**

#### **Thêm flag vào initialState:**

```javascript
const initialState = {
  // ... existing state
  showProfileCompletionModal: false,
  profileDataLoaded: false, // Thêm flag để track profile data đã load chưa
};
```

#### **Thêm reducer:**

```javascript
setProfileDataLoaded: (state, action) => {
  state.profileDataLoaded = action.payload;
},
```

### **2. Cập nhật Modal Logic**

#### **Trước:**

```javascript
checkAndShowProfileModal: state => {
  const user = state.user;

  // Only show modal if:
  // 1. User is authenticated
  // 2. Email is verified
  // 3. Profile is not complete
  // 4. Profile completion percentage is less than 80%
  const shouldShow = !!(
    state.isAuthenticated &&
    user?.is_email_verified &&
    !user?.is_profile_complete &&
    user?.profile_completion_percentage < 80
  );

  if (shouldShow) {
    state.showProfileCompletionModal = true;
  } else {
    state.showProfileCompletionModal = false;
  }
},
```

#### **Sau:**

```javascript
checkAndShowProfileModal: state => {
  const user = state.user;

  // Don't check modal if profile data hasn't loaded yet
  if (!state.profileDataLoaded) {
    console.log('🔍 checkAndShowProfileModal - Profile data not loaded yet, skipping check');
    return;
  }

  // Only show modal if:
  // 1. User is authenticated
  // 2. Profile data is loaded
  // 3. Email is verified
  // 4. Profile is not complete
  // 5. Profile completion percentage is less than 80%
  const shouldShow = !!(
    state.isAuthenticated &&
    state.profileDataLoaded &&
    user?.is_email_verified &&
    !user?.is_profile_complete &&
    user?.profile_completion_percentage < 80
  );

  if (shouldShow) {
    state.showProfileCompletionModal = true;
  } else {
    state.showProfileCompletionModal = false;
  }
},
```

### **3. Set Profile Data Loaded Flag**

#### **Trong login.fulfilled:**

```javascript
.addCase(login.fulfilled, (state, action) => {
  // ... existing logic

  // Set profile data as loaded
  state.profileDataLoaded = true;

  // Check if we should show profile completion modal using new logic
  authSlice.caseReducers.checkAndShowProfileModal(state);
})
```

#### **Trong ProfileCompletionModal:**

```javascript
if (statusData.status === "success") {
  setCompletionStatus(statusData.data);

  // Set profile data as loaded
  dispatch(setProfileDataLoaded(true));

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

## 🎯 **Kết quả**

### **Data Flow mới:**

```
1. User Login → profileDataLoaded: false
2. Profile Data Load → profileDataLoaded: true
3. checkAndShowProfileModal → Check với data đầy đủ
4. Modal hiện/ẩn → Quyết định chính xác
```

### **Tránh Flash Modal:**

- **Modal không hiện** cho đến khi profile data load xong
- **Quyết định chính xác** dựa trên data đầy đủ
- **Không có hiện tượng** hiện rồi ẩn

## 🚀 **Tính năng mới**

### **1. Profile Data Loading State**

- Track profile data đã load chưa
- Prevent modal check trước khi data sẵn sàng
- Better user experience

### **2. Conditional Modal Logic**

- Modal chỉ check khi data đã load
- Tránh flash modal
- Consistent behavior

### **3. Better Debug Logging**

- Log khi profile data chưa load
- Track profileDataLoaded state
- Easier debugging

## 🔄 **User Flow**

### **Trước (có flash):**

```
Load Page → Modal hiện → Data load → Modal ẩn (flash)
```

### **Sau (không flash):**

```
Load Page → Data load → Modal check → Modal hiện/ẩn (chính xác)
```

## 🎨 **UX Improvements**

1. **No Flash Modal**: Modal không hiện rồi ẩn
2. **Consistent Behavior**: Modal logic chính xác
3. **Better Loading**: Wait for data before showing modal
4. **Smooth Experience**: Không có jarring transitions

## 📱 **Technical Improvements**

1. **State Management**: Better state tracking
2. **Conditional Logic**: Modal chỉ check khi cần
3. **Performance**: Không check modal không cần thiết
4. **Debugging**: Better logging và tracking
