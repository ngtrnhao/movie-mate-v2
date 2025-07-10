import { useState } from 'react';
import { Info, Trash2 } from 'lucide-react';
import { useWatchlist } from '../../../hooks/useWatchlist';
import { useNavigate } from 'react-router-dom';

const WatchlistComponent = () => {
  const navigate = useNavigate();
  const {
    watchlists,
    loading,
    error,
    removeFromWatchlist,
    updateWatchlistStatus,
    loadWatchlistData,
  } = useWatchlist();

  const [sortBy, setSortBy] = useState('date'); // 'date', 'title', 'rating'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [updatingIds, setUpdatingIds] = useState(new Set());

  const handleStatusChange = async (watchlistId, movieId, newStatus) => {
    const updateId = `${movieId}-${newStatus}`;
    if (updatingIds.has(updateId)) return;
    setUpdatingIds(prev => new Set([...prev, updateId]));
    await updateWatchlistStatus(watchlistId, movieId, newStatus);
    setUpdatingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(updateId);
      return newSet;
    });
  };

  const handleRemove = async (watchlistId, movieId) => {
    const removeId = `${movieId}-remove`;
    if (updatingIds.has(removeId)) return;
    setUpdatingIds(prev => new Set([...prev, removeId]));
    await removeFromWatchlist(watchlistId, movieId);
    setUpdatingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(removeId);
      return newSet;
    });
  };

  const handleMovieClick = movieId => {
    navigate(`/movies/${movieId}`);
  };

  // Sorting function for items in a watchlist
  const sortItems = items => {
    return [...items].sort((a, b) => {
      const movieA = a.movie_data || {};
      const movieB = b.movie_data || {};
      switch (sortBy) {
        case 'title':
          return (movieA.title || '').localeCompare(movieB.title || '');
        case 'rating':
          return (movieB.rating || 0) - (movieA.rating || 0);
        case 'date':
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });
  };

  if (loading) {
    return (
      <div className="space-y-6 p-4">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-2xl font-bold text-white">My Watchlists</h3>
          <div className="h-8 w-32 animate-pulse rounded-lg bg-gray-700"></div>
        </div>
        <div className="space-y-8">
          {[...Array(2)].map((_, idx) => (
            <div key={idx}>
              <div className="mb-4 h-6 w-48 animate-pulse rounded bg-gray-700"></div>
              <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {[...Array(4)].map((_, index) => (
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
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6 p-4">
        <h3 className="text-2xl font-bold text-white">My Watchlists</h3>
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-red-400">
          <p className="text-lg">Error loading watchlists: {error}</p>
          <button
            onClick={loadWatchlistData}
            className="mt-4 rounded-lg bg-red-500 px-6 py-3 text-white transition-all hover:scale-105 hover:bg-red-600 active:scale-95"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  if (!watchlists || watchlists.length === 0) {
    return (
      <div className="space-y-6 p-4">
        <h3 className="text-2xl font-bold text-white">My Watchlists</h3>
        <div className="rounded-xl border border-gray-700 bg-gray-800/60 p-8 text-center text-gray-400">
          <p className="text-lg">You have no watchlists yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 p-4">
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <h3 className="text-2xl font-bold text-white">My Watchlists</h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center rounded-lg bg-gray-800 p-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`rounded-md px-3 py-1.5 transition-all ${viewMode === 'grid' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`rounded-md px-3 py-1.5 transition-all ${viewMode === 'list' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'}`}
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
      {watchlists.map(list => (
        <div key={list.id} className="space-y-4">
          <div className="mb-2 flex items-center gap-3">
            <h4 className="text-xl font-semibold text-white">{list.name}</h4>
            <span className="text-sm text-gray-400">({list.items.length} movies)</span>
          </div>
          {list.items.length === 0 ? (
            <div className="rounded-xl border border-gray-700 bg-gray-800/60 p-6 text-center text-gray-400">
              <p>No movies in this list.</p>
            </div>
          ) : (
            <div
              className={
                viewMode === 'grid'
                  ? 'grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
                  : 'flex flex-col gap-4'
              }
            >
              {sortItems(list.items).map(item => {
                const movie = item.movie_data || {};
                const movieId = movie.id || item.movie_id;
                const watchlistId = list.id;
                const isUpdating = Array.from(updatingIds).some(id => id.startsWith(movieId));
                return viewMode === 'grid' ? (
                  <div key={item.id} className="group relative">
                    <div
                      className="relative aspect-[2/3] cursor-pointer overflow-hidden rounded-xl shadow-lg transition-all duration-300 group-hover:scale-105"
                      onClick={() => handleMovieClick(movieId)}
                    >
                      <img
                        src={movie.poster_url || '/images/placeholder-movie.jpg'}
                        alt={movie.title}
                        className="size-full object-cover"
                        onError={e => {
                          e.target.src = '/images/placeholder-movie.jpg';
                        }}
                      />
                      {/* Overlay actions */}
                      <div className="absolute bottom-2 right-2 flex flex-col gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleMovieClick(movieId);
                          }}
                          className="rounded-lg bg-white/20 p-2 transition-all hover:scale-110 hover:bg-white/30"
                          title="View Details"
                        >
                          <Info size={18} className="text-white" />
                        </button>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleRemove(watchlistId, movieId);
                          }}
                          disabled={updatingIds.has(`${movieId}-remove`)}
                          className="rounded-lg bg-red-500/80 p-2 transition-all hover:scale-110 hover:bg-red-600/80 disabled:opacity-50"
                          title="Remove from Watchlist"
                        >
                          <Trash2 size={18} className="text-white" />
                        </button>
                      </div>
                      {/* Updating overlay */}
                      {isUpdating && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                          <div className="animate-pulse text-sm font-medium text-white">
                            Updating...
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="mt-3 space-y-1">
                      <h4
                        className="line-clamp-2 cursor-pointer text-sm font-medium text-white transition-colors hover:text-red-400"
                        onClick={() => handleMovieClick(movieId)}
                        title={movie.title}
                      >
                        {movie.title}
                      </h4>
                      <p className="text-xs text-gray-400">
                        Added {new Date(item.created_at).toLocaleDateString()}
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
                    key={item.id}
                    className="flex cursor-pointer gap-4 rounded-xl bg-gray-800/50 p-4 transition-all hover:bg-gray-800"
                    onClick={() => handleMovieClick(movieId)}
                  >
                    <img
                      src={movie.poster_url || '/images/placeholder-movie.jpg'}
                      alt={movie.title}
                      className="h-30 w-20 rounded-lg object-cover"
                      onError={e => {
                        e.target.src = '/images/placeholder-movie.jpg';
                      }}
                    />
                    <div className="flex-1">
                      <h4 className="font-medium text-white transition-colors hover:text-red-400">
                        {movie.title}
                      </h4>
                      <div className="mt-2 flex items-center gap-2">
                        {movie.rating && (
                          <div className="flex items-center gap-1 text-xs text-yellow-400">
                            <span>★</span>
                            <span>{movie.rating.toFixed(1)}</span>
                          </div>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-gray-400">
                        Added {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default WatchlistComponent;
