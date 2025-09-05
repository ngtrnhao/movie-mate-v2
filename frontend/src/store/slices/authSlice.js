import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  loginAPI,
  registerAPI,
  refreshTokenAPI,
  updateProfileAPI,
  forgotPasswordAPI,
  resetPasswordAPI,
} from '../../api/auth';
import adCooldownService from '../../services/adCooldownService';

const initialState = {
  user: {
    id: null,
    username: null,
    email: null,
    firstName: null,
    lastName: null,
    avatarUrl: null,
    bio: null,
    birth_date: null,
    age: null,
    age_group: null,
    gender: null,
    occupation: null,
    location: null,
    zip_code: null,
    createdAt: null,
    updatedAt: null,
    user_type: null,
    groups: [], // Thêm groups để lưu thông tin quyền
    is_profile_complete: false,
    profile_completion_percentage: 0,
  },
  isAuthenticated: false,
  isRehydrated: false,
  token: null,
  refreshToken: null,
  loading: false,
  error: null,
  rememberMe: false,
  userPreferences: {
    language: 'en',
    theme: 'dark',
  },
  showProfileCompletionModal: false,
  profileDataLoaded: false, // Thêm flag để track profile data đã load chưa
};

// Async Thunks
export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password, rememberMe }, { rejectWithValue }) => {
    try {
      const response = await loginAPI(email, password);
      if (rememberMe) {
        localStorage.setItem('token', response.access);
        localStorage.setItem('refreshToken', response.refresh);
      }
      return response;
    } catch (error) {
      const errorData = error.response?.data || {};
      let errorMessage = 'Login failed';

      if (errorData.code === 'email_not_verified') {
        errorMessage = 'Please verify your email before logging in.';
      } else if (errorData.code === 'invalid_password') {
        errorMessage = 'The password you entered is incorrect.';
      } else if (errorData.code === 'validation_error') {
        errorMessage = Object.values(errorData.message).join(', ');
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }

      return rejectWithValue(errorMessage);
    }
  }
);

export const register = createAsyncThunk('auth/register', async (userData, { rejectWithValue }) => {
  try {
    const response = await registerAPI(userData);
    return {
      ...response,
      user: {
        ...response.user, // Remove hardcoded isEmailVerified to use backend data

        avatarUrl: null,
        bio: null,
        age: null,
        gender: null,
        location: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        user_type: 'member',
      },
    };
  } catch (error) {
    return rejectWithValue(error.response?.data || 'Registration failed');
  }
});

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      const response = await refreshTokenAPI(refreshToken);
      localStorage.setItem('token', response.access);
      localStorage.setItem('refreshToken', response.refresh);
      return response;
    } catch (error) {
      // Clear localStorage on refresh failure
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      return rejectWithValue(error.response?.data || 'Token refresh failed');
    }
  }
);

export const updateProfile = createAsyncThunk(
  'auth/updateProfile',
  async (userData, { getState, rejectWithValue }) => {
    try {
      const { token } = getState().auth;
      const response = await updateProfileAPI(userData, token);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Profile update failed');
    }
  }
);

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email, { rejectWithValue }) => {
    try {
      const response = await forgotPasswordAPI(email);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Password reset request failed');
    }
  }
);

export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async ({ token, password, confirm_password }, { rejectWithValue }) => {
    try {
      const response = await resetPasswordAPI(token, password, confirm_password);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Password reset failed');
    }
  }
);

export const googleLogin = createAsyncThunk(
  'auth/googleLogin',
  async (userData, { rejectWithValue }) => {
    try {
      return userData;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Google login failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: state => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.loading = false;
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.access;
      state.refreshToken = action.payload.refresh;
      state.error = null;
      localStorage.setItem('token', action.payload.access);
      localStorage.setItem('refreshToken', action.payload.refresh);
      localStorage.setItem('user', JSON.stringify(action.payload.user));
    },
    loginFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload;
    },
    logout: state => {
      // Xóa dữ liệu quảng cáo
      adCooldownService.clearAll();

      state.user = {
        id: null,
        username: null,
        email: null,
        firstName: null,
        lastName: null,
        avatarUrl: null,
        bio: null,
        age: null,
        gender: null,
        location: null,
        // Remove hardcoded isEmailVerified to use backend data
        createdAt: null,
        updatedAt: null,
        user_type: null,
        groups: [],
      };
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
      // Clear all authentication data from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      // Clear any other auth-related data
      sessionStorage.clear();
    },
    clearError: state => {
      state.error = null;
    },
    setRememberMe: (state, action) => {
      state.rememberMe = action.payload;
    },
    updateUserPreferences: (state, action) => {
      state.userPreferences = {
        ...state.userPreferences,
        ...action.payload,
      };
    },
    /**
     * rehydrateAuth
     * Khôi phục trạng thái đăng nhập từ localStorage vào Redux state khi app khởi động hoặc reload.
     * Nếu localStorage có token và user, sẽ cập nhật lại state đăng nhập.
     */
    rehydrateAuth: state => {
      const token = localStorage.getItem('token');
      const refreshToken = localStorage.getItem('refreshToken');
      const user = localStorage.getItem('user');

      if (token && user) {
        try {
          const userData = JSON.parse(user);
          state.isAuthenticated = true;
          state.token = token;
          state.refreshToken = refreshToken;
          state.user = { ...initialState.user, ...userData };

          // Check if we should show profile completion modal after rehydration
          authSlice.caseReducers.checkAndShowProfileModal(state);
        } catch (error) {
          // If user data is corrupted, clear everything
          console.error('Failed to parse user data:', error);
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
        }
      }
      state.isRehydrated = true;
    },
    /**
     * clearAuthData
     * Clear all authentication data from localStorage and state
     */
    clearAuthData: state => {
      state.user = initialState.user;
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      sessionStorage.clear();
    },
    updateUser: (state, action) => {
      state.user = { ...state.user, ...action.payload };
      localStorage.setItem('user', JSON.stringify(state.user));
    },
    showProfileCompletionModal: state => {
      state.showProfileCompletionModal = true;
    },
    hideProfileCompletionModal: state => {
      state.showProfileCompletionModal = false;
    },
    updateProfileCompletion: (state, action) => {
      state.user.is_profile_complete = action.payload.is_profile_complete;
      state.user.profile_completion_percentage = action.payload.profile_completion_percentage;

      // Hide modal if profile is now complete
      if (action.payload.is_profile_complete) {
        state.showProfileCompletionModal = false;
      }
    },
    setProfileDataLoaded: (state, action) => {
      state.profileDataLoaded = action.payload;
    },
    // Helper function to check if profile completion modal should be shown
    checkAndShowProfileModal: state => {
      const user = state.user;

      // Don't check modal if profile data hasn't loaded yet
      if (!state.profileDataLoaded) {
        console.log('🔍 checkAndShowProfileModal - Profile data not loaded yet, skipping check');
        return;
      }

      // Debug logging
      console.log('🔍 checkAndShowProfileModal - Current state:', {
        isAuthenticated: state.isAuthenticated,
        userEmailVerified: user?.is_email_verified, // Use snake_case only
        userProfileComplete: user?.is_profile_complete,
        userCompletionPercentage: user?.profile_completion_percentage,
        userExists: !!user,
        userKeys: user ? Object.keys(user) : 'No user',
        userEmailVerifiedType: typeof user?.is_email_verified,
        userEmailVerifiedValue: user?.is_email_verified,
        userStringified: user ? JSON.stringify(user) : 'No user',
        profileDataLoaded: state.profileDataLoaded,
      });

      // Only show modal if:
      // 1. User is authenticated
      // 2. Profile data is loaded
      // 3. Email is verified
      // 4. Profile is not complete
      // 5. Profile completion percentage is less than 80%
      const shouldShow = !!(
        state.isAuthenticated &&
        state.profileDataLoaded &&
        user?.is_email_verified && // Use snake_case only
        !user?.is_profile_complete &&
        user?.profile_completion_percentage < 80
      );

      console.log('🔍 checkAndShowProfileModal - Should show modal:', shouldShow);

      if (shouldShow) {
        state.showProfileCompletionModal = true;
        console.log('✅ Modal will be shown');
      } else {
        state.showProfileCompletionModal = false;
        console.log('❌ Modal will be hidden');
      }
    },
  },
  extraReducers: builder => {
    builder
      // Login
      .addCase(login.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.access;
        state.refreshToken = action.payload.refresh;
        state.error = null;
        localStorage.setItem('token', action.payload.access);
        localStorage.setItem('refreshToken', action.payload.refresh);
        localStorage.setItem('user', JSON.stringify(action.payload.user));

        console.log('🔍 login.fulfilled - User data received:', {
          user: action.payload.user,
          isEmailVerified: action.payload.user?.is_email_verified, // Use snake_case only
          isProfileComplete: action.payload.user?.is_profile_complete,
          profileCompletionPercentage: action.payload.user?.profile_completion_percentage,
        });

        // Set profile data as loaded
        state.profileDataLoaded = true;

        // Check if we should show profile completion modal using new logic
        authSlice.caseReducers.checkAndShowProfileModal(state);
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Register
      .addCase(register.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.error = null;

        // For new users, don't show modal immediately - wait for email verification
        // Modal will be shown after email verification and login
        state.showProfileCompletionModal = false;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Refresh Token
      .addCase(refreshToken.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access;
        state.refreshToken = action.payload.refresh;
        state.error = null;
        localStorage.setItem('token', action.payload.access);
        localStorage.setItem('refreshToken', action.payload.refresh);
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        // Clear all auth data on refresh failure
        state.user = initialState.user;
        state.isAuthenticated = false;
        state.token = null;
        state.refreshToken = null;
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        sessionStorage.clear();
      })
      // Update Profile
      .addCase(updateProfile.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Forgot Password
      .addCase(forgotPassword.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(forgotPassword.fulfilled, state => {
        state.loading = false;
        state.error = null;
      })
      .addCase(forgotPassword.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Reset Password
      .addCase(resetPassword.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(resetPassword.fulfilled, state => {
        state.loading = false;
        state.error = null;
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Google Login
      .addCase(googleLogin.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(googleLogin.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.access;
        state.refreshToken = action.payload.refresh;
        state.error = null;
        localStorage.setItem('token', action.payload.access);
        localStorage.setItem('refreshToken', action.payload.refresh);
        localStorage.setItem('user', JSON.stringify(action.payload.user));
      })
      .addCase(googleLogin.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  clearError,
  setRememberMe,
  updateUserPreferences,
  rehydrateAuth,
  clearAuthData,
  updateUser,
  showProfileCompletionModal,
  hideProfileCompletionModal,
  updateProfileCompletion,
  setProfileDataLoaded,
  checkAndShowProfileModal,
} = authSlice.actions;

// Selectors
export const selectUser = state => state.auth.user;
export const selectIsAuthenticated = state => state.auth.isAuthenticated;
export const selectIsRehydrated = state => state.auth.isRehydrated;
export const selectToken = state => state.auth.token;
export const selectAuthLoading = state => state.auth.loading;
export const selectError = state => state.auth.error;

// Permission selectors
export const selectUserGroups = state => state.auth.user?.groups || [];
export const selectIsAdmin = state => {
  const groups = state.auth.user?.groups || [];
  return groups.some(group => group.name === 'Administrators');
};
export const selectIsModerator = state => {
  const groups = state.auth.user?.groups || [];
  return groups.some(group => group.name === 'Moderators');
};
export const selectHasAdminAccess = state => {
  const groups = state.auth.user?.groups || [];
  return groups.some(group => group.name === 'Administrators' || group.name === 'Moderators');
};

// Profile completion selectors
export const selectShowProfileCompletionModal = state => state.auth.showProfileCompletionModal;
export const selectIsProfileComplete = state => state.auth.user?.is_profile_complete || false;
export const selectProfileCompletionPercentage = state =>
  state.auth.user?.profile_completion_percentage || 0;
export const selectProfileDataLoaded = state => state.auth.profileDataLoaded;

export default authSlice.reducer;
