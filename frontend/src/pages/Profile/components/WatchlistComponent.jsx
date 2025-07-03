import { useState, useEffect } from 'react';
import { Clock, Eye, CheckCircle, MoreHorizontal, Info } from 'lucide-react';
import { useWatchlist } from '../../../hooks/useWatchlist';
import { useNavigate } from 'react-router-dom';

const WatchlistComponent = () => {
  const navigate = useNavigate();
  const {
    watchlist,
    loading,
    error,
    removeFromWatchlist,
    updateWatchlistStatus,
    getWatchlistByStatus,
    loadWatchlist,
  } = useWatchlist();

  const [activeTab, setActiveTab] = useState('PLANNED');
  const [updatingIds, setUpdatingIds] = useState(new Set());

  useEffect(() => {
    loadWatchlist();
  }, [loadWatchlist]);

  const tabs = [
    { id: 'PLANNED', label: 'Plan to Watch', icon: Clock, color: 'blue' },
    { id: 'WATCHING', label: 'Watching', icon: Eye, color: 'yellow' },
    { id: 'WATCHED', label: 'Watched', icon: CheckCircle, color: 'green' },
  ];

  const handleStatusChange = async (movieId, newStatus) => {
    const updateId = `${movieId}-${newStatus}`;
    if (updatingIds.has(updateId)) return;

    setUpdatingIds(prev => new Set([...prev, updateId]));
    const success = await updateWatchlistStatus(movieId, newStatus);

    setUpdatingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(updateId);
      return newSet;
    });
  };

  const handleRemove = async movieId => {
    const removeId = `${movieId}-remove`;
    if (updatingIds.has(removeId)) return;

    setUpdatingIds(prev => new Set([...prev, removeId]));
    const success = await removeFromWatchlist(movieId);

    setUpdatingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(removeId);
      return newSet;
    });
  };

  const handleMovieClick = movieId => {
    navigate(`/movies/${movieId}`);
  };

  const currentTabData = getWatchlistByStatus(activeTab);

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-xl font-semibold text-white">My Watchlist</h3>
        <div className="flex space-x-4 border-b border-gray-700">
          {tabs.map(tab => (
            <div key={tab.id} className="px-4 py-2 bg-gray-700 rounded animate-pulse">
              <div className="h-4 w-20 bg-gray-600 rounded"></div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {[...Array(6)].map((_, index) => (
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
        <h3 className="text-xl font-semibold text-white">My Watchlist</h3>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          <p>Error loading watchlist: {error}</p>
          <button
            onClick={loadWatchlist}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-white">My Watchlist</h3>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
        {tabs.map(tab => {
          const tabData = getWatchlistByStatus(tab.id);
          const count = tabData.length;
          const IconComponent = tab.icon;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              <IconComponent size={16} />
              {tab.label}
              {count > 0 && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    activeTab === tab.id ? 'bg-gray-600' : 'bg-gray-700'
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {currentTabData.length === 0 ? (
        <div className="text-center py-12">
          {(() => {
            const tab = tabs.find(t => t.id === activeTab);
            const IconComponent = tab.icon;
            return <IconComponent size={48} className="mx-auto text-gray-400 mb-4" />;
          })()}
          <p className="text-gray-400 text-lg mb-2">
            No movies in "{tabs.find(t => t.id === activeTab)?.label}"
          </p>
          <p className="text-gray-500 text-sm">Add movies to your watchlist to see them here</p>
          <button
            onClick={() => navigate('/movies')}
            className="mt-4 px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Browse Movies
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {currentTabData.map(item => {
            const movie = item.movie || {};
            const movieId = item.movie?.id || item.movie_id;

            return (
              <div key={item.id} className="group relative">
                {/* Movie Poster */}
                <div
                  className="relative aspect-[2/3] rounded-lg overflow-hidden cursor-pointer transition-transform duration-200 group-hover:scale-105"
                  onClick={() => handleMovieClick(movieId)}
                >
                  <img
                    src={movie.poster_url || '/images/placeholder-movie.jpg'}
                    alt={movie.title}
                    className="w-full h-full object-cover"
                    onError={e => {
                      e.target.src = '/images/placeholder-movie.jpg';
                    }}
                  />

                  {/* Status indicator */}
                  <div
                    className={`absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-medium ${
                      item.status === 'PLANNED'
                        ? 'bg-blue-500'
                        : item.status === 'WATCHING'
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                    } text-white`}
                  >
                    {tabs.find(t => t.id === item.status)?.label}
                  </div>

                  {/* Overlay with actions */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <div className="absolute top-2 right-2 space-y-2">
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
                    </div>

                    {/* Status change buttons */}
                    <div className="absolute bottom-2 left-2 right-2 space-y-1">
                      {tabs
                        .filter(tab => tab.id !== item.status)
                        .map(tab => {
                          const updateId = `${movieId}-${tab.id}`;
                          const isUpdating = updatingIds.has(updateId);

                          return (
                            <button
                              key={tab.id}
                              onClick={e => {
                                e.stopPropagation();
                                handleStatusChange(movieId, tab.id);
                              }}
                              disabled={isUpdating}
                              className="w-full p-2 bg-gray-800/80 hover:bg-gray-700/80 text-white text-xs rounded transition-colors disabled:opacity-50"
                            >
                              {isUpdating ? 'Updating...' : `Mark as ${tab.label}`}
                            </button>
                          );
                        })}

                      {/* Remove button */}
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          handleRemove(movieId);
                        }}
                        disabled={updatingIds.has(`${movieId}-remove`)}
                        className="w-full p-2 bg-red-500/80 hover:bg-red-600/80 text-white text-xs rounded transition-colors disabled:opacity-50"
                      >
                        {updatingIds.has(`${movieId}-remove`) ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Movie Info */}
                <div className="mt-2">
                  <h4
                    className="text-white text-sm font-medium line-clamp-2 cursor-pointer hover:text-red-400 transition-colors"
                    onClick={() => handleMovieClick(movieId)}
                    title={movie.title}
                  >
                    {movie.title}
                  </h4>
                  <p className="text-gray-400 text-xs mt-1">
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default WatchlistComponent;
