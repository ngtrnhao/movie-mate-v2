import axiosInstance from './axios';

export const getProfileAPI = async userId => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch profile' };
  }
};

//Update profile
export const updateProfileAPI = async (userId, userData) => {
  try {
    const response = await axiosInstance.put(`/api/auth/profile/${userId}/`, userData);
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      const errorData = error.response.data;
      if (typeof errorData === 'object') {
        const formattedError = {};
        Object.keys(errorData).forEach(key => {
          if (Array.isArray(errorData[key])) {
            formattedError[key] = errorData[key][0];
          } else {
            formattedError[key] = errorData[key];
          }
        });
        throw formattedError;
      }
      throw { error: 'Failed to update profile' };
    }
  }
};

//Upload profile avatar
export const uploadAvatarAPI = async (userId, formData) => {
  try {
    const response = await axiosInstance.post(`/api/auth/profile/${userId}/avatar/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to upload avatar' };
  }
};

//Statistics API
export const getUserStatsAPI = async userId => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/stats/`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch user statistics' };
  }
};

//Follow/Unfollow API
// export const followUserAPI = async (userId, followData) => {
//   try {
//     const response = await axiosInstance.post(`/users/follow/${userId}`, followData);
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { error: 'Failed to follow/unfollow user' };
//   }
// };

// //Get followers/following API
// export const getFollowersAPI = async userId => {
//   try {
//     const response = await axiosInstance.get(`/users/followers/${userId}`);
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { error: 'Failed to fetch followers/following' };
//   }
// };

// //Get watchlist history API
// export const getWatchedMoviesAPI = async (userId, page = 1) => {
//   try {
//     const response = await axiosInstance.get(`/users/watched/${userId}/watched-movies/`, {
//       params: { page },
//     });
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { error: 'Failed to fetch watched movies' };
//   }
// };

//Get review history API
export const getUserReviewsAPI = async (userId, page = 1) => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/reviews/`, {
      params: { page },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch user reviews' };
  }
};

//Get rating
export const getUserRatingsAPI = async (userId, page = 1) => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/ratings/`, {
      params: { page },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch user ratings' };
  }
};

//Get user favorite genre
export const getFavoriteGenresAPI = async (userId, page = 1) => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/favorite-genres/`, {
      params: { page },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Faileed to fetch favorite genres' };
  }
};
// //update profile settings
// export const updateProfileSettingsAPI = async (userId, settings) => {
//   try {
//     const response = await axiosInstance.put(`/users/profile/${userId}/settings/`, settings);
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { error: 'Failed to update profile settings' };
//   }
// };

// //delete Account
// export const deleteAccountAPI = async userId => {
//   try {
//     const response = await axiosInstance.delete(`/users/profile/${userId}`);
//     return response.data;
//   } catch (error) {
//     throw error.response?.data || { error: 'Failed to delete account' };
//   }
// };

//Get payment transaction
export const getPaymentTransactionAPI = async userId => {
  try {
    const response = await axiosInstance.get(`/api/subscriptions/payment-transaction/${userId}/`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch payment transaction' };
  }
};

//Create payment
export const createPaymentAPI = async paymentData => {
  try {
    const response = await axiosInstance.post('/api/subscriptions/create-payment/', paymentData);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to create payment' };
  }
};
