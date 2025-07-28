# Profile Completion Modal Logic Update

## 🎯 **Objective**

Điều chỉnh logic hiển thị profile completion modal để chỉ hiển thị sau khi người dùng đã verify email và dựa vào độ hoàn thiện của account.

## 🔧 **New Logic Implementation**

### **Conditions for Showing Modal**

Modal sẽ chỉ hiển thị khi **TẤT CẢ** các điều kiện sau được thỏa mãn:

1. ✅ **User is authenticated** - Người dùng đã đăng nhập
2. ✅ **Email is verified** - Email đã được xác thực
3. ✅ **Profile is not complete** - Hồ sơ chưa hoàn thiện
4. ✅ **Profile completion < 80%** - Độ hoàn thiện hồ sơ dưới 80%

### **Logic Flow**

```javascript
const shouldShowModal = () => {
  return (
    isAuthenticated &&
    user.isEmailVerified &&
    !user.is_profile_complete &&
    user.profile_completion_percentage < 80
  );
};
```

## 📁 **Files Updated**

### 1. **`frontend/src/store/slices/authSlice.js`**

**Added new reducer:**

```javascript
checkAndShowProfileModal: (state) => {
  const user = state.user;

  // Only show modal if all conditions are met
  if (
    state.isAuthenticated &&
    user.isEmailVerified &&
    !user.is_profile_complete &&
    user.profile_completion_percentage < 80
  ) {
    state.showProfileCompletionModal = true;
  } else {
    state.showProfileCompletionModal = false;
  }
};
```

**Updated login.fulfilled:**

```javascript
.addCase(login.fulfilled, (state, action) => {
  // ... existing logic ...

  // Check if we should show profile completion modal using new logic
  authSlice.caseReducers.checkAndShowProfileModal(state);
})
```

**Updated register.fulfilled:**

```javascript
.addCase(register.fulfilled, (state, action) => {
  // ... existing logic ...

  // For new users, don't show modal immediately - wait for email verification
  // Modal will be shown after email verification and login
  state.showProfileCompletionModal = false;
})
```

**Updated rehydrateAuth:**

```javascript
rehydrateAuth: (state) => {
  // ... existing logic ...

  // Check if we should show profile completion modal after rehydration
  authSlice.caseReducers.checkAndShowProfileModal(state);
};
```

### 2. **`frontend/src/components/auth/EmailVerificationChecker.jsx`**

**New component to monitor email verification status:**

```javascript
const EmailVerificationChecker = () => {
  // Check email verification status every 30 seconds
  // Update user data if email verification status changed
  // Trigger modal visibility check
};
```

**Features:**

- ✅ Monitors email verification status changes
- ✅ Updates user data in Redux when status changes
- ✅ Triggers modal visibility check
- ✅ Runs every 30 seconds automatically
- ✅ Invisible component (doesn't render anything)

### 3. **`frontend/src/hooks/useProfileCompletionModal.js`**

**Custom hook for modal management:**

```javascript
export const useProfileCompletionModal = () => {
  // Provides:
  // - showModal: current modal visibility state
  // - shouldShowModal: calculated visibility based on conditions
  // - checkModalVisibility: function to manually check visibility
  // - user, isAuthenticated: current user state
};
```

### 4. **`frontend/src/App.jsx`**

**Added EmailVerificationChecker:**

```javascript
{/* Email Verification Checker */}
<EmailVerificationChecker />

{/* Profile Completion Modal */}
<ProfileCompletionModal ... />
```

### 5. **`frontend/src/components/modals/ProfileCompletionModal.jsx`**

**Added debug logging:**

```javascript
useEffect(() => {
  if (open && user) {
    console.log("Profile Completion Modal Conditions:", {
      isAuthenticated: true,
      isEmailVerified: user.isEmailVerified,
      isProfileComplete: user.is_profile_complete,
      profileCompletionPercentage: user.profile_completion_percentage,
      shouldShowModal:
        user.isEmailVerified &&
        !user.is_profile_complete &&
        user.profile_completion_percentage < 80,
    });
  }
}, [open, user]);
```

## 🔄 **User Journey Flow**

### **New User Registration:**

1. User registers → `showProfileCompletionModal = false`
2. User receives verification email
3. User verifies email → `isEmailVerified = true`
4. User logs in → Modal visibility check triggered
5. If profile incomplete → Modal shows

### **Existing User Login:**

1. User logs in → Modal visibility check triggered
2. If email verified + profile incomplete → Modal shows
3. If email not verified → Modal hidden
4. If profile complete → Modal hidden

### **Email Verification After Login:**

1. User logs in with unverified email → Modal hidden
2. User verifies email → EmailVerificationChecker detects change
3. User data updated → Modal visibility check triggered
4. If profile incomplete → Modal shows

## 📊 **Profile Completion Calculation**

### **Required Fields (80% threshold):**

- ✅ `birth_date` - Required
- ✅ `gender` - Required
- ✅ `occupation` - Required
- ✅ `first_name` - Optional but recommended
- ✅ `last_name` - Optional but recommended
- ✅ `location` - Optional
- ✅ `zip_code` - Optional
- ✅ `bio` - Optional

### **Completion Percentage:**

```javascript
// 8 total fields
// 3 required fields (birth_date, gender, occupation) = 37.5% each
// 5 optional fields = 12.5% each
// 80% threshold = At least 3 required fields + 2 optional fields
```

## 🎯 **Expected Behavior**

### **Modal Shows When:**

- ✅ User authenticated + Email verified + Profile incomplete + Completion < 80%
- ✅ User verifies email after login (if profile incomplete)
- ✅ User data changes (if conditions met)

### **Modal Hides When:**

- ✅ User not authenticated
- ✅ Email not verified
- ✅ Profile is complete
- ✅ Profile completion ≥ 80%
- ✅ User manually closes modal

### **Debug Information:**

- ✅ Console logs show current conditions
- ✅ Console logs show modal visibility decision
- ✅ Console logs show email verification status changes

## 🔧 **Testing Scenarios**

### **Test Case 1: New User Registration**

1. Register new user
2. Verify modal doesn't show immediately
3. Verify email
4. Login
5. Verify modal shows (if profile incomplete)

### **Test Case 2: Existing User with Unverified Email**

1. Login with unverified email
2. Verify modal doesn't show
3. Verify email
4. Verify modal shows (if profile incomplete)

### **Test Case 3: User with Complete Profile**

1. Login with verified email + complete profile
2. Verify modal doesn't show

### **Test Case 4: User with High Completion Percentage**

1. Login with verified email + 85% completion
2. Verify modal doesn't show

## 🎉 **Benefits**

1. **✅ Better UX**: Modal only shows when relevant
2. **✅ Email Verification Required**: Ensures user engagement
3. **✅ Smart Timing**: Shows at appropriate moments
4. **✅ Automatic Monitoring**: Real-time status checking
5. **✅ Debug Friendly**: Comprehensive logging
6. **✅ Flexible Threshold**: 80% completion threshold
7. **✅ Non-Intrusive**: Doesn't block user flow

## 🔄 **Future Enhancements**

1. **Configurable Threshold**: Make 80% threshold configurable
2. **Progressive Disclosure**: Show different steps based on completion level
3. **Incentive System**: Show benefits of profile completion
4. **A/B Testing**: Test different thresholds and timing
5. **Analytics**: Track modal effectiveness and completion rates
