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
export const getUserRatings = async (userId, page = 1, language = 'vi') => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/ratings/`, {
      params: { page, language },
    });

    // Standardize response format
    const responseData = response.data;
    return {
      results: responseData.results || responseData.data || [],
      data: responseData.results || responseData.data || [],
      count: responseData.count || 0,
      next: responseData.next || null,
      previous: responseData.previous || null,
      status: responseData.status || 'success',
    };
  } catch (error) {
    throw new Error('Failed to fetch user ratings');
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

// Get user favorite movies
export const getFavoriteMoviesAPI = async (userId, page = 1) => {
  try {
    const response = await axiosInstance.get(`/api/auth/profile/${userId}/favorite-movies/`, {
      params: { page },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch favorite movies' };
  }
};

// Add movie to favorites - Alternative approach for current backend
export const addToFavoritesAPI = async movieId => {
  try {
    // Ensure movieId is a number
    const parsedMovieId = parseInt(movieId);
    if (isNaN(parsedMovieId)) {
      throw new Error(`Invalid movie ID: ${movieId}`);
    }

    console.log('🚀 API Call: Adding to favorites', { movieId, parsedMovieId });

    const response = await axiosInstance.post('/api/auth/favorite-movies/', {
      movie: parsedMovieId, // Use 'movie' field which is the foreign key
    });
    console.log('✅ API Response: Add to favorites', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ API Error: Add to favorites failed', {
      movieId,
      error: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText,
      fullError: error,
    });
    throw error.response?.data || { error: 'Failed to add movie to favorites' };
  }
};

// Remove movie from favorites
export const removeFromFavoritesAPI = async favoriteId => {
  try {
    const response = await axiosInstance.delete(`/api/auth/favorite-movies/${favoriteId}/`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to remove movie from favorites' };
  }
};

// Check if movie is in favorites
export const checkFavoriteStatusAPI = async movieId => {
  try {
    const response = await axiosInstance.get('/api/auth/favorite-movies/', {
      params: { movie: movieId },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to check favorite status' };
  }
};

// Get user watchlist
export const getWatchlistAPI = async (page = 1) => {
  try {
    const response = await axiosInstance.get('/api/auth/watchlist/', {
      params: { page },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch watchlist' };
  }
};

// Get all watchlists
export const getWatchlistsAPI = async () => {
  try {
    const response = await axiosInstance.get('/api/auth/watchlist/');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to add movie to watchlist' };
  }
};

// Add movie to existing watchlist
export const addMovieToWatchlistAPI = async (watchlistId, movieId) => {
  try {
    const response = await axiosInstance.post(`/api/auth/watchlist/${watchlistId}/movies/`, {
      movie: movieId,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to add movie to watchlist' };
  }
};

// Create new watchlist
export const addToWatchlistAPI = async (movieId, status = 'PLANNED', name = null) => {
  try {
    const response = await axiosInstance.post('/api/auth/watchlist/', {
      movie_id: movieId,
      status,
      name,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to add movie to watchlist' };
  }
};

// Update watchlist status
export const updateWatchlistStatusAPI = async (watchlistId, status) => {
  try {
    const response = await axiosInstance.patch(`/api/auth/watchlist/${watchlistId}/`, {
      status: status,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to update watchlist status' };
  }
};

// Remove movie from watchlist
export const removeFromWatchlistAPI = async watchlistId => {
  try {
    const response = await axiosInstance.delete(`/api/auth/watchlist/${watchlistId}/`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to remove movie from watchlist' };
  }
};

// Check if movie is in watchlist
export const checkWatchlistStatusAPI = async movieId => {
  try {
    const response = await axiosInstance.get('/api/auth/watchlist/', {
      params: { movie: movieId },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to check watchlist status' };
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
