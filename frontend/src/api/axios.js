import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // Tăng timeout lên 30 giây
});

// Request interceptor
axiosInstance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('token', access);

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // If refresh token fails, clear all auth data and redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');

        // Only redirect if we're not already on the login or home page
        if (
          !window.location.pathname.includes('/login') &&
          !window.location.pathname.includes('/home')
        ) {
          window.location.href = '/home';
        }
        return Promise.reject(refreshError);
      }
    }

    // Handle timeout and connection errors
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
      if (!originalRequest._retry) {
        originalRequest._retry = true;
        // Tăng thời gian chờ giữa các lần retry
        await new Promise(resolve => setTimeout(resolve, 2000));
        return axiosInstance(originalRequest);
      }
    }

    // Log error details for debugging
    console.error('API Error:', {
      url: originalRequest.url,
      method: originalRequest.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
    });

    return Promise.reject(error);
  }
);

export { axiosInstance };
export default axiosInstance;
