import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useFavorites } from '../../hooks/useFavorites';
import { testFavoritesAPI } from '../../utils/testFavorites';
import {
  addToFavorites as addToFavoritesAction,
  loadFavorites,
} from '../../store/slices/favoritesSlice';

const FavoritesDebugPanel = ({ movieId, movieData }) => {
  const dispatch = useDispatch();
  const authState = useSelector(state => state.auth);
  const favoritesState = useSelector(state => state.favorites);
  const { addToFavorites, isFavorited } = useFavorites();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleTestAdd = async () => {
    console.log('🧪 Debug: Testing add to favorites');
    const result = await addToFavorites(movieId, movieData);
    console.log('🧪 Debug: Add result:', result);
  };

  const handleDirectAPITest = async () => {
    console.log('🧪 Debug: Testing API directly');
    await testFavoritesAPI();
  };

  const handleDirectReduxTest = async () => {
    console.log('🧪 Debug: Testing Redux action directly');
    const result = await dispatch(addToFavoritesAction({ movieId, movieData }));
    console.log('🧪 Debug: Direct Redux result:', result);
  };

  const handleLoadFavorites = async () => {
    console.log('🧪 Debug: Loading favorites');
    if (authState.user?.id) {
      const result = await dispatch(loadFavorites(authState.user.id));
      console.log('🧪 Debug: Load favorites result:', result);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md rounded-lg bg-black/90 p-4 text-white">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-lg font-bold">Favorites Debug Panel</h3>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded bg-gray-700 px-2 py-1 text-sm hover:bg-gray-600"
        >
          {isCollapsed ? 'Show' : 'Hide'}
        </button>
      </div>

      {!isCollapsed && (
        <div className="space-y-2 text-sm">
          <div>
            <strong>Auth State:</strong>
            <pre className="mt-1 max-h-20 overflow-auto rounded bg-gray-800 p-2 text-xs">
              {JSON.stringify(
                {
                  isAuthenticated: authState.isAuthenticated,
                  isRehydrated: authState.isRehydrated,
                  user: authState.user
                    ? {
                        id: authState.user.id,
                        username: authState.user.username,
                        email: authState.user.email,
                      }
                    : null,
                  hasToken: !!authState.token,
                  localStorageToken: !!localStorage.getItem('token'),
                  localStorageUser: !!localStorage.getItem('user'),
                },
                null,
                2
              )}
            </pre>
          </div>

          <div>
            <strong>Favorites State:</strong>
            <pre className="mt-1 max-h-20 overflow-auto rounded bg-gray-800 p-2 text-xs">
              {JSON.stringify(
                {
                  count: favoritesState.items?.length || 0,
                  loading: favoritesState.loading,
                  error: favoritesState.error,
                  initialized: favoritesState.initialized,
                  favoriteIds: favoritesState.favoriteIds
                    ? Array.from(favoritesState.favoriteIds)
                    : [],
                },
                null,
                2
              )}
            </pre>
          </div>

          <div>
            <strong>Movie Info:</strong>
            <pre className="mt-1 max-h-20 overflow-auto rounded bg-gray-800 p-2 text-xs">
              {JSON.stringify(
                {
                  movieId,
                  movieIdType: typeof movieId,
                  isFavorited: isFavorited(movieId),
                  movieTitle: movieData?.title,
                },
                null,
                2
              )}
            </pre>
          </div>

          <div className="space-y-1">
            <button
              onClick={handleTestAdd}
              className="w-full rounded bg-blue-600 px-2 py-1 text-white hover:bg-blue-700"
            >
              Test useFavorites Hook
            </button>

            <button
              onClick={handleDirectAPITest}
              className="w-full rounded bg-green-600 px-2 py-1 text-white hover:bg-green-700"
            >
              Test API Directly
            </button>

            <button
              onClick={handleDirectReduxTest}
              className="w-full rounded bg-purple-600 px-2 py-1 text-white hover:bg-purple-700"
            >
              Test Redux Action
            </button>

            <button
              onClick={handleLoadFavorites}
              className="w-full rounded bg-orange-600 px-2 py-1 text-white hover:bg-orange-700"
            >
              Load Favorites
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FavoritesDebugPanel;
