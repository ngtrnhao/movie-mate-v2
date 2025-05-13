import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Login API
export const loginAPI = async (email, password) => {
  const response = await axios.post(`${API_URL}/auth/login/`, {
    email,
    password,
  });
  return response.data;
};

// Register API
export const registerAPI = async (userData) => {
  const response = await axios.post(`${API_URL}/auth/register/`, userData);
  return response.data;
};

// Refresh Token API
export const refreshTokenAPI = async (refreshToken) => {
  const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
    refresh: refreshToken,
  });
  return response.data;
};

// Update Profile API
export const updateProfileAPI = async (userData, token) => {
  const response = await axios.put(`${API_URL}/auth/profile/`, userData, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
};

// Forgot Password API
export const forgotPasswordAPI = async (email) => {
  const response = await axios.post(`${API_URL}/auth/password-reset/`, {
    email,
  });
  return response.data;
};

// Reset Password API
export const resetPasswordAPI = async (token, password) => {
  const response = await axios.post(`${API_URL}/auth/password-reset/confirm/`, {
    token,
    password,
  });
  return response.data;
};
