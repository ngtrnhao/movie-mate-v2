import axiosInstance from '../api/axios';

// Test function to check favorites API endpoints
export const testFavoritesAPI = async () => {
  console.log('🧪 Testing Favorites API...');

  try {
    // Check authentication
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    console.log('🔍 Auth check:', {
      hasToken: !!token,
      userId: user.id,
      userName: user.username,
    });

    if (!token || !user.id) {
      console.error('❌ Not authenticated');
      return;
    }

    // Test 1: Get existing favorites
    console.log('🔍 Test 1: Getting existing favorites...');
    try {
      const favoritesResponse = await axiosInstance.get('/api/auth/favorite-movies/');
      console.log('✅ Get favorites success:', favoritesResponse.data);
    } catch (error) {
      console.error('❌ Get favorites failed:', error.response?.data);
    }

    // Test 2: Try to add a movie to favorites (using movie ID 1 as test)
    const testMovieId = 1;
    console.log(`🔍 Test 2: Adding movie ${testMovieId} to favorites...`);
    try {
      const addResponse = await axiosInstance.post('/api/auth/favorite-movies/', {
        movie: testMovieId,
      });
      console.log('✅ Add to favorites success:', addResponse.data);

      // Test 3: Remove the added favorite
      console.log('🔍 Test 3: Removing from favorites...');
      const favoriteId = addResponse.data.id;
      const removeResponse = await axiosInstance.delete(`/api/auth/favorite-movies/${favoriteId}/`);
      console.log('✅ Remove from favorites success:', removeResponse.status);
    } catch (error) {
      console.error('❌ Add/Remove favorites failed:', {
        status: error.response?.status,
        data: error.response?.data,
        config: error.config,
      });
    }
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
};

// Add to window for browser console access
if (typeof window !== 'undefined') {
  window.testFavoritesAPI = testFavoritesAPI;
}
