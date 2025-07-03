import { useState, useEffect } from 'react';
import { Heart, MoreHorizontal, Play, Info } from 'lucide-react';
import { useFavorites } from '../../../hooks/useFavorites';
import { useNavigate } from 'react-router-dom';

const FavoritesList = () => {
  const navigate = useNavigate();
  const { favorites, loading, error, removeFromFavorites, loadFavorites } = useFavorites();

  const [removingIds, setRemovingIds] = useState(new Set());

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const handleRemove = async (movieId, favoriteId) => {
    if (removingIds.has(movieId)) return;

    setRemovingIds(prev => new Set([...prev, movieId]));
    const result = await removeFromFavorites(movieId);

    // Always remove from removingIds after operation
    setRemovingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(movieId);
      return newSet;
    });

    if (!result.success) {
      console.error('Failed to remove from favorites:', result.error);
      // You might want to show a toast notification here
    }
  };

  const handleMovieClick = movieId => {
    navigate(`/movies/${movieId}`);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-white">Favorite Movies</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {[...Array(10)].map((_, index) => (
            <div key={index} className="animate-pulse">
              <div className="aspect-[2/3] bg-gray-700 rounded-lg"></div>
              <div className="mt-2 h-4 bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-white">Favorite Movies</h3>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          <p>Error loading favorites: {error}</p>
          <button
            onClick={loadFavorites}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!favorites || favorites.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-white">Favorite Movies</h3>
        <div className="text-center py-12">
          <Heart size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-400 text-lg mb-2">No favorite movies yet</p>
          <p className="text-gray-500 text-sm">
            Start adding movies to your favorites to see them here
          </p>
          <button
            onClick={() => navigate('/movies')}
            className="mt-4 px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Browse Movies
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-white">Favorite Movies ({favorites.length})</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {favorites.map(favorite => {
          const movie = favorite.movie || {};
          const movieId = favorite.movie_id || movie.id;
          const isRemoving = removingIds.has(movieId);

          return (
            <div key={favorite.id} className="group relative">
              {/* Movie Poster */}
              <div
                className="relative aspect-[2/3] rounded-lg overflow-hidden cursor-pointer transition-transform duration-200 group-hover:scale-105"
                onClick={() => handleMovieClick(movieId)}
              >
                <img
                  src={favorite.movie_poster || movie.poster_url || '/images/placeholder-movie.jpg'}
                  alt={favorite.movie_title || movie.title}
                  className="w-full h-full object-cover"
                  onError={e => {
                    e.target.src = '/images/placeholder-movie.jpg';
                  }}
                />

                {/* Overlay with actions */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center space-x-2">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleMovieClick(movieId);
                    }}
                    className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                    title="View Details"
                  >
                    <Info size={16} className="text-white" />
                  </button>

                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleRemove(movieId, favorite.id);
                    }}
                    disabled={isRemoving}
                    className="p-2 bg-red-500/80 rounded-full hover:bg-red-600/80 transition-colors disabled:opacity-50"
                    title="Remove from Favorites"
                  >
                    <Heart
                      size={16}
                      className={`text-white ${isRemoving ? 'animate-pulse' : ''}`}
                      fill="currentColor"
                    />
                  </button>
                </div>

                {/* Favorite indicator */}
                <div className="absolute top-2 right-2 p-1 bg-pink-500 rounded-full">
                  <Heart size={12} className="text-white" fill="currentColor" />
                </div>

                {/* Removing overlay */}
                {isRemoving && (
                  <div className="absolute inset-0 bg-black/80 flex items-center justify-center">
                    <div className="text-white text-sm">Removing...</div>
                  </div>
                )}
              </div>

              {/* Movie Info */}
              <div className="mt-2">
                <h4
                  className="text-white text-sm font-medium line-clamp-2 cursor-pointer hover:text-red-400 transition-colors"
                  onClick={() => handleMovieClick(movieId)}
                  title={favorite.movie_title || movie.title}
                >
                  {favorite.movie_title || movie.title}
                </h4>
                <p className="text-gray-400 text-xs mt-1">
                  Added {new Date(favorite.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FavoritesList;
