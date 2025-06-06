import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

class AuthService {
  async login(email, password) {
    try {
      const response = await axios.post(`${API_URL}/api/auth/login/`, {
        email,
        password,
      });

      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  async googleLogin(accessToken) {
    try {
      const response = await axios.post(`${API_URL}/api/auth/google/`, {
        access_token: accessToken,
      });

      if (response.data.access) {
        localStorage.setItem('token', response.data.access);
        localStorage.setItem('refreshToken', response.data.refresh);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }

      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  logout() {
    localStorage.removeItem('user');
  }

  getCurrentUser() {
    return JSON.parse(localStorage.getItem('user'));
  }
}

export default new AuthService();
