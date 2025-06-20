import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getProfileAPI,
  updateProfileAPI,
  uploadAvatarAPI,
  getUserStatsAPI,
  // followUserAPI,
  // getFollowersAPI,
  // getWatchedMoviesAPI,
  getUserReviewsAPI,
  getUserRatingsAPI,
  getFavoriteGenresAPI,
  // updateProfileSettingsAPI,
  // deleteAccountAPI,
} from '../../api/profileService';

//Async Thunk
export const fetchProfile = createAsyncThunk('profile/fetchProfile', async userId => {
  const response = await getProfileAPI(userId);
  return response;
});

export const updateProfile = createAsyncThunk(
  'profile/updateProfile',
  async ({ userId, userData }) => {
    const response = await updateProfileAPI(userId, userData);
    return response;
  }
);

export const uploadAvatar = createAsyncThunk(
  'profile/uploadAvatar',
  async ({ userId, formData }) => {
    const response = await uploadAvatarAPI(userId, formData);
    return response;
  }
);

export const fetchUserStats = createAsyncThunk('profile/fetchUserStats', async userId => {
  const response = await getUserStatsAPI(userId);
  return response;
});

// export const fetchFollowers = createAsyncThunk('profile/fetchFollowers', async userId => {
//   const response = await followUserAPI(userId);
//   return response;
// });

// export const fetchFollowing = createAsyncThunk('profile/fetchFollowing', async userId => {
//   const response = await getFollowersAPI(userId);
//   return response;
// });

// export const fetchWatchedMovies = createAsyncThunk(
//   'profile/fetchWatchedMovies',
//   async (userId, page = 1) => {
//     const response = await getWatchedMoviesAPI(userId, page);
//     return response;
//   }
// );

export const fetchUserReviews = createAsyncThunk(
  'profile/fetchUserReviews',
  async (userId, page = 1) => {
    const response = await getUserReviewsAPI(userId, page);
    return response;
  }
);

export const fetchUserRatings = createAsyncThunk(
  'profile/fetchUserRatings',
  async (userId, page = 1) => {
    const response = await getUserRatingsAPI(userId, page);
    return response;
  }
);

export const fetchFavoriteGenres = createAsyncThunk(
  'profile/fetchFavoriteGenres',
  async (userId, page = 1) => {
    const response = await getFavoriteGenresAPI(userId, page);
    return response;
  }
);

// export const updateProfileSettings = createAsyncThunk(
//   'profile/updateProfileSettings',
//   async (userId, settings) => {
//     const response = await updateProfileSettingsAPI(userId, settings);
//     return response;
//   }
// );

// export const deleteAccount = createAsyncThunk('profile/deleteAccount', async userId => {
//   const response = await deleteAccountAPI(userId);
//   return response;
// });

const initialState = {
  data: null,
  stats: null,
  watchedMovies: {
    items: [],
    total: 0,
    currentPage: 1,
    hasMore: false,
  },
  reviews: {
    items: [],
    total: 0,
    currentPage: 1,
    hasMore: false,
  },
  ratings: {
    items: [],
    total: 0,
    currentPage: 1,
    hasMore: false,
  },
  favoriteGenres: [],
  settings: null,
  loading: {
    profile: false,
    stats: false,
    watchedMovies: false,
    reviews: false,
    ratings: false,
    genres: false,
    settings: false,
  },
  error: {
    profile: null,
    stats: null,
    watchedMovies: null,
    reviews: null,
    ratings: null,
    genres: null,
    settings: null,
  },
};

//Slices
const profileSlice = createSlice({
  name: 'profile',
  initialState,
  reducers: {
    clearProfile: () => {
      return initialState;
    },
    clearError: (state, action) => {
      if (action.payload) {
        state.error[action.payload] = null;
      } else {
        state.error = initialState.error;
      }
    },
    setCurrentPage: (state, action) => {
      const { type, page } = action.payload;
      state[type].currentPage = page;
    },
  },
  extraReducers: builder => {
    builder
      //Fetch Profile
      .addCase(fetchProfile.pending, state => {
        state.loading.profile = true;
        state.error.profile = null;
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.loading.profile = false;
        state.data = action.payload;
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        state.loading.profile = false;
        state.error.profile = action.error.message;
      })
      //Update Profile
      .addCase(updateProfile.pending, state => {
        state.loading.profile = true;
        state.error.profile = null;
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.loading.profile = false;
        state.data = { ...state.data, ...action.payload };
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.loading.profile = false;
        state.error.profile = action.error.message;
      })
      //Upload Avatar
      .addCase(uploadAvatar.pending, state => {
        state.loading.profile = true;
        state.error.profile = null;
      })
      .addCase(uploadAvatar.fulfilled, (state, action) => {
        state.loading.profile = false;
        state.data = { ...state.data, avatar_url: action.payload.avatar_url };
      })
      .addCase(uploadAvatar.rejected, (state, action) => {
        state.loading.profile = false;
        state.error.profile = action.error.message;
      })

      //Fetch User Stats
      .addCase(fetchUserStats.pending, state => {
        state.loading.stats = true;
        state.error.stats = null;
      })
      .addCase(fetchUserStats.fulfilled, (state, action) => {
        state.loading.stats = false;
        state.stats = action.payload;
      })
      .addCase(fetchUserStats.rejected, (state, action) => {
        state.loading.stats = false;
        state.error.stats = action.error.message;
      })

      //Fetch Watched Movies
      // .addCase(fetchWatchedMovies.pending, state => {
      //   state.loading.watchedMovies = true;
      //   state.error.watchedMovies = null;
      // })
      // .addCase(fetchWatchedMovies.fulfilled, (state, action) => {
      //   state.loading.watchedMovies = false;
      //   state.watchedMovies = {
      //     items: [...state.watchedMovies.items, ...action.payload.results],
      //     total: action.payload.count,
      //     currentPage: action.payload.current_page,
      //     hasMore: action.payload.next !== null,
      //   };
      // })
      // .addCase(fetchWatchedMovies.rejected, (state, action) => {
      //   state.loading.watchedMovies = false;
      //   state.error.watchedMovies = action.error.message;
      // })
      //Fetch User Reviews
      .addCase(fetchUserReviews.pending, state => {
        state.loading.reviews = true;
        state.error.reviews = null;
      })
      .addCase(fetchUserReviews.fulfilled, (state, action) => {
        state.loading.reviews = false;
        state.reviews = {
          items: [...state.reviews.items, ...action.payload.results],
          total: action.payload.count,
          currentPage: action.payload.current_page,
          hasMore: action.payload.next !== null,
        };
      })
      .addCase(fetchUserReviews.rejected, (state, action) => {
        state.loading.reviews = false;
        state.error.reviews = action.error.message;
      })
      //Fetch User Ratings
      .addCase(fetchUserRatings.pending, state => {
        state.loading.ratings = true;
        state.error.ratings = null;
      })
      .addCase(fetchUserRatings.fulfilled, (state, action) => {
        state.loading.ratings = false;
        state.ratings = {
          items: [...state.ratings.items, ...action.payload.results],
          total: action.payload.count,
          currentPage: action.payload.current_page,
          hasMore: action.payload.next !== null,
        };
      })
      .addCase(fetchUserRatings.rejected, (state, action) => {
        state.loading.ratings = false;
        state.error.ratings = action.error.message;
      })
      //Fetch Favorite Genres
      .addCase(fetchFavoriteGenres.pending, state => {
        state.loading.genres = true;
        state.error.genres = null;
      })
      .addCase(fetchFavoriteGenres.fulfilled, (state, action) => {
        state.loading.genres = false;
        state.favoriteGenres = action.payload.results || [];
      })
      .addCase(fetchFavoriteGenres.rejected, (state, action) => {
        state.loading.genres = false;
        state.error.genres = action.error.message;
      });
    //Update Profile Settings
    // .addCase(updateProfileSettings.pending, state => {
    //   state.loading.settings = true;
    //   state.error.settings = null;
    // })
    // .addCase(updateProfileSettings.fulfilled, (state, action) => {
    //   state.loading.settings = false;
    //   state.settings = action.payload;
    // })
    // .addCase(updateProfileSettings.rejected, (state, action) => {
    //   state.loading.settings = false;
    //   state.error.settings = action.error.message;
    // })
    // //Delete Account
    // .addCase(deleteAccount.pending, state => {
    //   state.loading.profile = true;
    //   state.error.profile = null;
    // })
    // .addCase(deleteAccount.fulfilled, state => {
    //   state.loading.profile = false;
    // });
  },
});

//Actions
export const { clearProfile, clearError, setCurrentPage } = profileSlice.actions;
export default profileSlice.reducer;
