import { useState, useEffect } from 'react';
import { Heart, Info } from 'lucide-react';
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
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-2xl font-bold text-white">Favorite Movies</h3>
          <div className="h-8 w-32 animate-pulse rounded-lg bg-gray-700"></div>
        </div>
        <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {[...Array(10)].map((_, index) => (
            <div key={index} className="animate-pulse">
              <div className="aspect-[2/3] rounded-xl bg-gray-700 shadow-lg"></div>
              <div className="mt-3 space-y-2">
                <div className="h-4 w-3/4 rounded bg-gray-700"></div>
                <div className="h-3 w-1/2 rounded bg-gray-700"></div>
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
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-red-400">
          <p className="text-lg">Error loading favorites: {error}</p>
          <button
            onClick={loadFavorites}
            className="mt-4 rounded-lg bg-red-500 px-6 py-3 text-white transition-all hover:scale-105 hover:bg-red-600 active:scale-95"
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
        <div className="rounded-xl border border-gray-700 bg-gray-800/50 py-16 text-center">
          <Heart size={64} className="mx-auto mb-6 animate-pulse text-red-400" />
          <p className="mb-3 text-xl font-medium text-gray-200">No favorite movies yet</p>
          <p className="mb-6 text-base text-gray-400">
            Start exploring and add movies to your favorites collection
          </p>
          <button
            onClick={() => navigate('/movies')}
            className="rounded-lg bg-red-500 px-8 py-3 text-white shadow-lg transition-all hover:scale-105 hover:bg-red-600 active:scale-95"
          >
            Discover Movies
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <h3 className="text-2xl font-bold text-white">
          Favorite Movies
          <span className="ml-2 text-lg text-gray-400">({favorites.length})</span>
        </h3>

        <div className="flex items-center gap-4">
          <div className="flex items-center rounded-lg bg-gray-800 p-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === 'grid' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === 'list' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              List
            </button>
          </div>

          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500"
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
            ? 'grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
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
                className="relative aspect-[2/3] cursor-pointer overflow-hidden rounded-xl shadow-lg transition-all duration-300 group-hover:scale-105"
                onClick={() => handleMovieClick(movieId)}
              >
                <img
                  src={favorite.movie_poster || movie.poster_url || 'https://placehold.co/600x400'}
                  alt={favorite.movie_title || movie.title}
                  className="size-full object-cover"
                  onError={e => {
                    e.target.src = 'https://placehold.co/600x400';
                  }}
                />

                <div className="absolute inset-0 flex items-center justify-center gap-3 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 transition-all duration-300 group-hover:opacity-100">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleMovieClick(movieId);
                    }}
                    className="rounded-full bg-white/20 p-3 transition-all hover:scale-110 hover:bg-white/30"
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
                    className="rounded-full bg-red-500/80 p-3 transition-all hover:scale-110 hover:bg-red-600/80 disabled:opacity-50"
                    title="Remove from Favorites"
                  >
                    <Heart
                      size={20}
                      className={`text-white ${isRemoving ? 'animate-pulse' : ''}`}
                      fill="currentColor"
                    />
                  </button>
                </div>

                <div className="absolute right-3 top-3 rounded-full bg-red-500 p-1.5 shadow-lg">
                  <Heart size={14} className="text-white" fill="currentColor" />
                </div>

                {isRemoving && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="animate-pulse text-sm font-medium text-white">Removing...</div>
                  </div>
                )}
              </div>

              <div className="mt-3 space-y-1">
                <h4
                  className="line-clamp-2 cursor-pointer text-sm font-medium text-white transition-colors hover:text-red-400"
                  onClick={() => handleMovieClick(movieId)}
                  title={favorite.movie_title || movie.title}
                >
                  {favorite.movie_title || movie.title}
                </h4>
                <p className="text-xs text-gray-400">
                  Added {new Date(favorite.created_at).toLocaleDateString()}
                </p>
                {movie.rating && (
                  <div className="flex items-center gap-1 text-xs text-yellow-400">
                    <span>★</span>
                    <span>{movie.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div
              key={favorite.id}
              className="flex cursor-pointer gap-4 rounded-xl bg-gray-800/50 p-4 transition-all hover:bg-gray-800"
              onClick={() => handleMovieClick(movieId)}
            >
              <img
                src={favorite.movie_poster || movie.poster_url || 'https://placehold.co/600x400'}
                alt={favorite.movie_title || movie.title}
                className="h-30 w-20 rounded-lg object-cover"
                onError={e => {
                  e.target.src = 'https://placehold.co/600x400';
                }}
              />
              <div className="flex-1">
                <h4 className="font-medium text-white transition-colors hover:text-red-400">
                  {favorite.movie_title || movie.title}
                </h4>
                <p className="mt-1 text-sm text-gray-400">
                  Added {new Date(favorite.created_at).toLocaleDateString()}
                </p>
                {movie.rating && (
                  <div className="mt-1 flex items-center gap-1 text-sm text-yellow-400">
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
                  className="rounded-full bg-red-500/80 p-2 transition-all hover:bg-red-600/80 disabled:opacity-50"
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
