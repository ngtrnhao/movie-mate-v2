import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  fetchPersonalizedRecommendations,
  fetchCollaborativeRecommendations,
  fetchDemographicRecommendations,
  fetchHybridRecommendations,
  submitRecommendationFeedback,
  fetchUserRecommendationProfile,
} from '../../api/recommendationService';

// Async thunks for recommendation actions
export const loadPersonalizedRecommendations = createAsyncThunk(
  'recommendations/loadPersonalized',
  async ({ context = 'homepage', limit = 20, refresh = false }, { rejectWithValue }) => {
    try {
      const response = await fetchPersonalizedRecommendations({ context, limit, refresh });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: 'Failed to load recommendations' });
    }
  }
);

export const loadCollaborativeRecommendations = createAsyncThunk(
  'recommendations/loadCollaborative',
  async ({ context = 'homepage', limit = 20, refresh = false }, { rejectWithValue }) => {
    try {
      const response = await fetchCollaborativeRecommendations({ context, limit, refresh });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { message: 'Failed to load collaborative recommendations' }
      );
    }
  }
);

export const loadDemographicRecommendations = createAsyncThunk(
  'recommendations/loadDemographic',
  async ({ context = 'homepage', limit = 20, refresh = false }, { rejectWithValue }) => {
    try {
      const response = await fetchDemographicRecommendations({ context, limit, refresh });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { message: 'Failed to load demographic recommendations' }
      );
    }
  }
);

export const loadHybridRecommendations = createAsyncThunk(
  'recommendations/loadHybrid',
  async ({ context = 'homepage', limit = 20, refresh = false }, { rejectWithValue }) => {
    try {
      const response = await fetchHybridRecommendations({ context, limit, refresh });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { message: 'Failed to load hybrid recommendations' }
      );
    }
  }
);

export const submitFeedback = createAsyncThunk(
  'recommendations/submitFeedback',
  async ({ movieId, recommendationType, context, feedbackType, action }, { rejectWithValue }) => {
    try {
      const response = await submitRecommendationFeedback({
        movie_id: movieId,
        recommendation_type: recommendationType,
        context,
        feedback_type: feedbackType,
        action,
      });
      return { movieId, feedbackType, action, ...response.data };
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: 'Failed to submit feedback' });
    }
  }
);

export const loadUserProfile = createAsyncThunk(
  'recommendations/loadUserProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetchUserRecommendationProfile();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: 'Failed to load user profile' });
    }
  }
);

const initialState = {
  // Recommendations by type and context
  recommendations: {
    homepage: {
      personalized: [],
      collaborative: [],
      demographic: [],
      hybrid: [],
    },
    onboarding: {
      personalized: [],
      demographic: [],
      popular: [],
    },
  },

  // Hero banner recommendation (single movie)
  heroBannerMovie: null,

  // User recommendation profile
  userProfile: {
    cluster: null,
    preferences: {},
    demographicInfo: {},
    recentRecommendations: [],
  },

  // Loading states
  loading: {
    personalized: false,
    collaborative: false,
    demographic: false,
    hybrid: false,
    userProfile: false,
    feedback: false,
  },

  // Error states
  error: {
    personalized: null,
    collaborative: null,
    demographic: null,
    hybrid: null,
    userProfile: null,
    feedback: null,
  },

  // Metadata
  lastUpdated: {
    personalized: null,
    collaborative: null,
    demographic: null,
    hybrid: null,
  },

  // Feedback tracking
  feedbackSubmitted: {},

  // Cache management
  cacheInfo: {},

  // Recommendation type preference for this user
  preferredType: 'personalized',

  // UI state
  isInitialized: false,
};

const recommendationSlice = createSlice({
  name: 'recommendations',
  initialState,
  reducers: {
    clearRecommendations: (state, action) => {
      const { context = 'homepage', type = 'all' } = action.payload || {};

      if (type === 'all') {
        state.recommendations[context] = {
          personalized: [],
          collaborative: [],
          demographic: [],
          hybrid: [],
        };
      } else {
        state.recommendations[context][type] = [];
      }
    },

    clearErrors: state => {
      state.error = {
        personalized: null,
        collaborative: null,
        demographic: null,
        hybrid: null,
        userProfile: null,
        feedback: null,
      };
    },

    setHeroBannerMovie: (state, action) => {
      state.heroBannerMovie = action.payload;
    },

    setPreferredRecommendationType: (state, action) => {
      state.preferredType = action.payload;
    },

    markMovieClicked: (state, action) => {
      const { movieId, recommendationType, context } = action.payload;
      const key = `${movieId}_${recommendationType}_${context}`;
      state.feedbackSubmitted[key] = { clicked: true, timestamp: new Date().toISOString() };
    },

    markMovieRated: (state, action) => {
      const { movieId, recommendationType, context } = action.payload;
      const key = `${movieId}_${recommendationType}_${context}`;
      if (state.feedbackSubmitted[key]) {
        state.feedbackSubmitted[key].rated = true;
      } else {
        state.feedbackSubmitted[key] = { rated: true, timestamp: new Date().toISOString() };
      }
    },

    // Reset all recommendation state
    resetRecommendations: state => {
      return {
        ...initialState,
        userProfile: state.userProfile, // Keep user profile
      };
    },
  },

  extraReducers: builder => {
    builder
      // Personalized recommendations
      .addCase(loadPersonalizedRecommendations.pending, state => {
        state.loading.personalized = true;
        state.error.personalized = null;
      })
      .addCase(loadPersonalizedRecommendations.fulfilled, (state, action) => {
        state.loading.personalized = false;
        const context = action.meta.arg.context || 'homepage';
        state.recommendations[context] = state.recommendations[context] || {};
        state.recommendations[context].personalized = action.payload.movies || [];
        state.lastUpdated.personalized = new Date().toISOString();
        state.cacheInfo.personalized = action.payload.cached || false;

        // Set hero banner movie from first recommendation
        if (context === 'homepage' && action.payload.movies && action.payload.movies.length > 0) {
          state.heroBannerMovie = action.payload.movies[0];
        }

        state.isInitialized = true;
      })
      .addCase(loadPersonalizedRecommendations.rejected, (state, action) => {
        state.loading.personalized = false;
        state.error.personalized =
          action.payload?.message || 'Failed to load personalized recommendations';
      })

      // Collaborative recommendations
      .addCase(loadCollaborativeRecommendations.pending, state => {
        state.loading.collaborative = true;
        state.error.collaborative = null;
      })
      .addCase(loadCollaborativeRecommendations.fulfilled, (state, action) => {
        state.loading.collaborative = false;
        const context = action.meta.arg.context || 'homepage';
        state.recommendations[context] = state.recommendations[context] || {};
        state.recommendations[context].collaborative = action.payload.movies || [];
        state.lastUpdated.collaborative = new Date().toISOString();
        state.cacheInfo.collaborative = action.payload.cached || false;
      })
      .addCase(loadCollaborativeRecommendations.rejected, (state, action) => {
        state.loading.collaborative = false;
        state.error.collaborative =
          action.payload?.message || 'Failed to load collaborative recommendations';
      })

      // Demographic recommendations
      .addCase(loadDemographicRecommendations.pending, state => {
        state.loading.demographic = true;
        state.error.demographic = null;
      })
      .addCase(loadDemographicRecommendations.fulfilled, (state, action) => {
        state.loading.demographic = false;
        const context = action.meta.arg.context || 'homepage';
        state.recommendations[context] = state.recommendations[context] || {};
        state.recommendations[context].demographic = action.payload.movies || [];
        state.lastUpdated.demographic = new Date().toISOString();
        state.cacheInfo.demographic = action.payload.cached || false;

        // Store cluster info in user profile
        if (action.payload.cluster_info) {
          state.userProfile.cluster = action.payload.cluster_info;
        }
      })
      .addCase(loadDemographicRecommendations.rejected, (state, action) => {
        state.loading.demographic = false;
        state.error.demographic =
          action.payload?.message || 'Failed to load demographic recommendations';
      })

      // Hybrid recommendations
      .addCase(loadHybridRecommendations.pending, state => {
        state.loading.hybrid = true;
        state.error.hybrid = null;
      })
      .addCase(loadHybridRecommendations.fulfilled, (state, action) => {
        state.loading.hybrid = false;
        const context = action.meta.arg.context || 'homepage';
        state.recommendations[context] = state.recommendations[context] || {};
        state.recommendations[context].hybrid = action.payload.movies || [];
        state.lastUpdated.hybrid = new Date().toISOString();
        state.cacheInfo.hybrid = action.payload.cached || false;
      })
      .addCase(loadHybridRecommendations.rejected, (state, action) => {
        state.loading.hybrid = false;
        state.error.hybrid = action.payload?.message || 'Failed to load hybrid recommendations';
      })

      // User profile
      .addCase(loadUserProfile.pending, state => {
        state.loading.userProfile = true;
        state.error.userProfile = null;
      })
      .addCase(loadUserProfile.fulfilled, (state, action) => {
        state.loading.userProfile = false;
        state.userProfile = action.payload;
      })
      .addCase(loadUserProfile.rejected, (state, action) => {
        state.loading.userProfile = false;
        state.error.userProfile = action.payload?.message || 'Failed to load user profile';
      })

      // Feedback submission
      .addCase(submitFeedback.pending, state => {
        state.loading.feedback = true;
        state.error.feedback = null;
      })
      .addCase(submitFeedback.fulfilled, (state, action) => {
        state.loading.feedback = false;
        const { movieId, feedbackType, action: feedbackAction } = action.payload;
        const key = `${movieId}_feedback`;
        state.feedbackSubmitted[key] = {
          ...state.feedbackSubmitted[key],
          [feedbackAction]: true,
          feedbackType,
          timestamp: new Date().toISOString(),
        };
      })
      .addCase(submitFeedback.rejected, (state, action) => {
        state.loading.feedback = false;
        state.error.feedback = action.payload?.message || 'Failed to submit feedback';
      });
  },
});

export const {
  clearRecommendations,
  clearErrors,
  setHeroBannerMovie,
  setPreferredRecommendationType,
  markMovieClicked,
  markMovieRated,
  resetRecommendations,
} = recommendationSlice.actions;

export default recommendationSlice.reducer;
