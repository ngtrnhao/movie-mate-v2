import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  loginAPI,
  registerAPI,
  refreshTokenAPI,
  updateProfileAPI,
  forgotPasswordAPI,
  resetPasswordAPI,
} from '../../api/auth';

const initialState = {
  user: {
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
    isEmailVerified: false,
    createdAt: null,
    updatedAt: null,
    user_type: null,
  },
  isAuthenticated: false,
  token: null,
  refreshToken: null,
  loading: false,
  error: null,
  rememberMe: false,
  userPreferences: {
    language: 'en',
    theme: 'dark',
  },
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
        ...response.user,
        isEmailVerified: false,
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
      const { refreshToken } = getState().auth;
      const response = await refreshTokenAPI(refreshToken);
      localStorage.setItem('token', response.access);
      localStorage.setItem('refreshToken', response.refresh);
      return response;
    } catch (error) {
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
        isEmailVerified: false,
        createdAt: null,
        updatedAt: null,
        user_type: null,
      };
      state.isAuthenticated = false;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
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
      const user = JSON.parse(localStorage.getItem('user'));
      if (token && user) {
        state.isAuthenticated = true;
        state.token = token;
        state.refreshToken = refreshToken;
        state.user = { ...initialState.user, ...user };
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
        state.isAuthenticated = false;
        state.token = null;
        state.refreshToken = null;
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
} = authSlice.actions;

export default authSlice.reducer;
