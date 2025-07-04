import { useState, useEffect } from 'react';
import { Heart, MoreHorizontal, Play, Info, Filter, SortAsc } from 'lucide-react';
import { useFavorites } from '../../../hooks/useFavorites';
import { useNavigate } from 'react-router-dom';

const FavoritesList = () => {
  const navigate = useNavigate();
  const { favorites, loading, error, removeFromFavorites, loadFavorites } = useFavorites();
  const [removingIds, setRemovingIds] = useState(new Set());
  const [sortBy, setSortBy] = useState('date'); // 'date', 'title', 'rating'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const handleRemove = async (movieId, favoriteId) => {
    if (removingIds.has(movieId)) return;

    setRemovingIds(prev => new Set([...prev, movieId]));
    const result = await removeFromFavorites(movieId);

    setRemovingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(movieId);
      return newSet;
    });

    if (!result.success) {
      console.error('Failed to remove from favorites:', result.error);
    }
  };

  const handleMovieClick = movieId => {
    navigate(`/movies/${movieId}`);
  };

  const sortedFavorites = [...(favorites || [])].sort((a, b) => {
    switch (sortBy) {
      case 'title':
        return (a.movie_title || a.movie?.title || '').localeCompare(
          b.movie_title || b.movie?.title || ''
        );
      case 'rating':
        return (b.movie?.rating || 0) - (a.movie?.rating || 0);
      case 'date':
      default:
        return new Date(b.created_at) - new Date(a.created_at);
    }
  });

  if (loading) {
    return (
      <div className="space-y-4 p-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white">Favorite Movies</h3>
          <div className="animate-pulse w-32 h-8 bg-gray-700 rounded-lg"></div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {[...Array(10)].map((_, index) => (
            <div key={index} className="animate-pulse">
              <div className="aspect-[2/3] bg-gray-700 rounded-xl shadow-lg"></div>
              <div className="mt-3 space-y-2">
                <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                <div className="h-3 bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 p-4">
        <h3 className="text-2xl font-bold text-white">Favorite Movies</h3>
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-red-400">
          <p className="text-lg">Error loading favorites: {error}</p>
          <button
            onClick={loadFavorites}
            className="mt-4 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all transform hover:scale-105 active:scale-95"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  if (!favorites || favorites.length === 0) {
    return (
      <div className="space-y-4 p-4">
        <h3 className="text-2xl font-bold text-white">Favorite Movies</h3>
        <div className="text-center py-16 bg-gray-800/50 rounded-xl border border-gray-700">
          <Heart size={64} className="mx-auto text-red-400 mb-6 animate-pulse" />
          <p className="text-gray-200 text-xl font-medium mb-3">No favorite movies yet</p>
          <p className="text-gray-400 text-base mb-6">
            Start exploring and add movies to your favorites collection
          </p>
          <button
            onClick={() => navigate('/movies')}
            className="px-8 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all transform hover:scale-105 active:scale-95 shadow-lg"
          >
            Discover Movies
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h3 className="text-2xl font-bold text-white">
          Favorite Movies
          <span className="ml-2 text-lg text-gray-400">({favorites.length})</span>
        </h3>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-gray-800 rounded-lg p-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'grid' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'list' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              List
            </button>
          </div>

          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="bg-gray-800 text-gray-200 rounded-lg px-4 py-2 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="date">Sort by Date Added</option>
            <option value="title">Sort by Title</option>
            <option value="rating">Sort by Rating</option>
          </select>
        </div>
      </div>

      <div
        className={
          viewMode === 'grid'
            ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6'
            : 'flex flex-col gap-4'
        }
      >
        {sortedFavorites.map(favorite => {
          const movie = favorite.movie || {};
          const movieId = favorite.movie_id || movie.id;
          const isRemoving = removingIds.has(movieId);

          return viewMode === 'grid' ? (
            <div key={favorite.id} className="group relative">
              <div
                className="relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer transition-all duration-300 group-hover:scale-105 shadow-lg"
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

                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-3">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleMovieClick(movieId);
                    }}
                    className="p-3 bg-white/20 rounded-full hover:bg-white/30 transition-all transform hover:scale-110"
                    title="View Details"
                  >
                    <Info size={20} className="text-white" />
                  </button>

                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleRemove(movieId, favorite.id);
                    }}
                    disabled={isRemoving}
                    className="p-3 bg-red-500/80 rounded-full hover:bg-red-600/80 transition-all transform hover:scale-110 disabled:opacity-50"
                    title="Remove from Favorites"
                  >
                    <Heart
                      size={20}
                      className={`text-white ${isRemoving ? 'animate-pulse' : ''}`}
                      fill="currentColor"
                    />
                  </button>
                </div>

                <div className="absolute top-3 right-3 p-1.5 bg-red-500 rounded-full shadow-lg">
                  <Heart size={14} className="text-white" fill="currentColor" />
                </div>

                {isRemoving && (
                  <div className="absolute inset-0 bg-black/80 flex items-center justify-center backdrop-blur-sm">
                    <div className="text-white text-sm font-medium animate-pulse">Removing...</div>
                  </div>
                )}
              </div>

              <div className="mt-3 space-y-1">
                <h4
                  className="text-white text-sm font-medium line-clamp-2 cursor-pointer hover:text-red-400 transition-colors"
                  onClick={() => handleMovieClick(movieId)}
                  title={favorite.movie_title || movie.title}
                >
                  {favorite.movie_title || movie.title}
                </h4>
                <p className="text-gray-400 text-xs">
                  Added {new Date(favorite.created_at).toLocaleDateString()}
                </p>
                {movie.rating && (
                  <div className="flex items-center gap-1 text-yellow-400 text-xs">
                    <span>★</span>
                    <span>{movie.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div
              key={favorite.id}
              className="flex gap-4 bg-gray-800/50 rounded-xl p-4 hover:bg-gray-800 transition-all cursor-pointer"
              onClick={() => handleMovieClick(movieId)}
            >
              <img
                src={favorite.movie_poster || movie.poster_url || '/images/placeholder-movie.jpg'}
                alt={favorite.movie_title || movie.title}
                className="w-20 h-30 object-cover rounded-lg"
                onError={e => {
                  e.target.src = '/images/placeholder-movie.jpg';
                }}
              />
              <div className="flex-1">
                <h4 className="text-white font-medium hover:text-red-400 transition-colors">
                  {favorite.movie_title || movie.title}
                </h4>
                <p className="text-gray-400 text-sm mt-1">
                  Added {new Date(favorite.created_at).toLocaleDateString()}
                </p>
                {movie.rating && (
                  <div className="flex items-center gap-1 text-yellow-400 text-sm mt-1">
                    <span>★</span>
                    <span>{movie.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={e => {
                    e.stopPropagation();
                    handleRemove(movieId, favorite.id);
                  }}
                  disabled={isRemoving}
                  className="p-2 bg-red-500/80 rounded-full hover:bg-red-600/80 transition-all disabled:opacity-50"
                  title="Remove from Favorites"
                >
                  <Heart
                    size={16}
                    className={`text-white ${isRemoving ? 'animate-pulse' : ''}`}
                    fill="currentColor"
                  />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FavoritesList;
