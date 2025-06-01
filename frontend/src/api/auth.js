import axiosInstance from './axios';

// Login API
export const loginAPI = async (email, password) => {
  try {
    const response = await axiosInstance.post('/auth/login/', {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to login' };
  }
};

// Register API
export const registerAPI = async (userData) => {
  try {
    const response = await axiosInstance.post('/auth/register/', {
      username: userData.username,
      email: userData.email,
      password: userData.password,
      password2: userData.confirmPassword,
    });
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      const errorData = error.response.data;
      if (typeof errorData === 'object') {
        const formattedErrors = {};
        Object.keys(errorData).forEach((key) => {
          if (Array.isArray(errorData[key])) {
            formattedErrors[key] = errorData[key][0];
          } else {
            formattedErrors[key] = errorData[key];
          }
        });
        throw formattedErrors;
      }
      throw errorData;
    }
    throw { error: 'Failed to register. Please try again.' };
  }
};

// Refresh Token API
export const refreshTokenAPI = async (refreshToken) => {
  const response = await axiosInstance.post('/auth/token/refresh/', {
    refresh: refreshToken,
  });
  return response.data;
};

// Forgot Password API
export const forgotPasswordAPI = async (email) => {
  const response = await axiosInstance.post('/auth/forgot-password/', {
    email,
  });
  return response.data;
};

// Reset Password API
export const resetPasswordAPI = async (token, password, confirm_password) => {
  const response = await axiosInstance.post('/auth/reset-password/', {
    token,
    password,
    confirm_password,
  });
  return response.data;
};

// Get User Profile
export const getProfileAPI = async () => {
  const response = await axiosInstance.get('/auth/profile/');
  return response.data;
};

// Update User Profile
export const updateProfileAPI = async (userData) => {
  const response = await axiosInstance.put('/auth/profile/', userData);
  return response.data;
};

export const verifyEmailAPI = async (token) => {
  try {
    const response = await axiosInstance.get(`/auth/verify-email/?token=${token}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to verify email' };
  }
};
