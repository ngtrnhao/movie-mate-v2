import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { getDashboardOverview } from '../../api/adminMovieService';

// Async thunk for fetching dashboard data
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchData',
  async (_, { rejectWithValue }) => {
    try {
      const data = await getDashboardOverview();
      return data;
    } catch (error) {
      return rejectWithValue(error.message || 'Không thể tải dữ liệu dashboard');
    }
  }
);

const initialState = {
  data: {
    total_movies: 0,
    published_movies: 0,
    pending_approval: 0,
    admin_featured: 0,
    quality_issues: 0,
    recent_movies: [],
  },
  loading: false,
  error: null,
  lastUpdated: null,
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearDashboardError: state => {
      state.error = null;
    },
  },
  extraReducers: builder => {
    builder
      .addCase(fetchDashboardData.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearDashboardError } = dashboardSlice.actions;

// Selectors
export const selectDashboardData = state => state.dashboard.data;
export const selectDashboardLoading = state => state.dashboard.loading;
export const selectDashboardError = state => state.dashboard.error;
export const selectDashboardLastUpdated = state => state.dashboard.lastUpdated;

export default dashboardSlice.reducer;
