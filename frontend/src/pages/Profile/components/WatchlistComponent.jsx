import { useState, useEffect } from 'react';
import {
  Clock,
  Eye,
  CheckCircle,
  MoreHorizontal,
  Info,
  Trash2,
  Filter,
  SortAsc,
} from 'lucide-react';
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
    loadWatchlistData,
  } = useWatchlist();

  const [activeTab, setActiveTab] = useState('PLANNED');
  const [updatingIds, setUpdatingIds] = useState(new Set());
  const [sortBy, setSortBy] = useState('date'); // 'date', 'title', 'rating'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  useEffect(() => {
    loadWatchlistData();
  }, [loadWatchlistData]);

  const tabs = [
    {
      id: 'PLANNED',
      label: 'Plan to Watch',
      icon: Clock,
      color: 'blue',
      bgColor: 'bg-blue-500',
      hoverBg: 'hover:bg-blue-600',
    },
    {
      id: 'WATCHING',
      label: 'Watching',
      icon: Eye,
      color: 'yellow',
      bgColor: 'bg-yellow-500',
      hoverBg: 'hover:bg-yellow-600',
    },
    {
      id: 'WATCHED',
      label: 'Watched',
      icon: CheckCircle,
      color: 'green',
      bgColor: 'bg-green-500',
      hoverBg: 'hover:bg-green-600',
    },
  ];

  const handleStatusChange = async (watchlistId, movieId, newStatus) => {
    const updateId = `${movieId}-${newStatus}`;
    if (updatingIds.has(updateId)) return;

    setUpdatingIds(prev => new Set([...prev, updateId]));
    const success = await updateWatchlistStatus(watchlistId, movieId, newStatus);

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
    const success = await removeFromWatchlist(watchlistId, movieId);

    setUpdatingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(removeId);
      return newSet;
    });
  };

  const handleMovieClick = movieId => {
    navigate(`/movies/${movieId}`);
  };

  const sortedWatchlist = [...(getWatchlistByStatus(activeTab) || [])].sort((a, b) => {
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

  if (loading) {
    return (
      <div className="space-y-6 p-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white">My Watchlist</h3>
          <div className="animate-pulse w-32 h-8 bg-gray-700 rounded-lg"></div>
        </div>

        <div className="flex space-x-4 overflow-x-auto pb-2">
          {tabs.map(tab => (
            <div key={tab.id} className="px-6 py-3 bg-gray-700/50 rounded-xl animate-pulse">
              <div className="h-4 w-24 bg-gray-600 rounded"></div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {[...Array(6)].map((_, index) => (
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
      <div className="space-y-6 p-4">
        <h3 className="text-2xl font-bold text-white">My Watchlist</h3>
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-red-400">
          <p className="text-lg">Error loading watchlist: {error}</p>
          <button
            onClick={loadWatchlistData}
            className="mt-4 px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all transform hover:scale-105 active:scale-95"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h3 className="text-2xl font-bold text-white">
          My Watchlist
          <span className="ml-2 text-lg text-gray-400">
            ({getWatchlistByStatus(activeTab).length})
          </span>
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

      {/* Tabs */}
      <div className="flex space-x-3 overflow-x-auto pb-2">
        {tabs.map(tab => {
          const tabData = getWatchlistByStatus(tab.id);
          const count = tabData.length;
          const IconComponent = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-6 py-3 rounded-xl text-sm font-medium transition-all transform hover:scale-105 ${
                isActive
                  ? `${tab.bgColor} text-white shadow-lg`
                  : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <IconComponent size={18} className={isActive ? 'animate-pulse' : ''} />
              <span>{tab.label}</span>
              {count > 0 && (
                <span
                  className={`px-2 py-1 rounded-lg text-xs ${isActive ? 'bg-white/20' : 'bg-gray-700'}`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {sortedWatchlist.length === 0 ? (
        <div className="text-center py-16 bg-gray-800/50 rounded-xl border border-gray-700">
          {(() => {
            const tab = tabs.find(t => t.id === activeTab);
            const IconComponent = tab.icon;
            return (
              <IconComponent
                size={64}
                className={`mx-auto mb-6 ${tab.id === 'PLANNED' ? 'text-blue-400' : tab.id === 'WATCHING' ? 'text-yellow-400' : 'text-green-400'} animate-pulse`}
              />
            );
          })()}
          <p className="text-gray-200 text-xl font-medium mb-3">
            No movies in "{tabs.find(t => t.id === activeTab)?.label}"
          </p>
          <p className="text-gray-400 text-base mb-6">
            Start exploring and add movies to your watchlist
          </p>
          <button
            onClick={() => navigate('/movies')}
            className="px-8 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all transform hover:scale-105 active:scale-95 shadow-lg"
          >
            Discover Movies
          </button>
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6'
              : 'flex flex-col gap-4'
          }
        >
          {sortedWatchlist.map(item => {
            const movie = item.movie_data || {};
            const movieId = movie.id;
            const watchlistId = item.watchlist;
            const currentTab = tabs.find(t => t.id === item.status);
            const isUpdating = Array.from(updatingIds).some(id => id.startsWith(movieId));

            return viewMode === 'grid' ? (
              <div key={item.id} className="group relative">
                <div
                  className="relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer transition-all duration-300 group-hover:scale-105 shadow-lg"
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

                  {/* Status badge */}
                  <div
                    className={`absolute top-3 left-3 px-3 py-1.5 rounded-lg text-xs font-medium ${currentTab.bgColor} text-white shadow-lg`}
                  >
                    <div className="flex items-center gap-2">
                      <currentTab.icon size={14} />
                      <span>{currentTab.label}</span>
                    </div>
                  </div>

                  {/* Actions Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <div className="absolute bottom-0 left-0 right-0 p-4 space-y-2">
                      <div className="flex items-center justify-center gap-2">
                        {tabs
                          .filter(tab => tab.id !== item.status)
                          .map(tab => (
                            <button
                              key={tab.id}
                              onClick={e => {
                                e.stopPropagation();
                                handleStatusChange(watchlistId, movieId, tab.id);
                              }}
                              disabled={updatingIds.has(`${movieId}-${tab.id}`)}
                              className={`p-2 rounded-lg ${tab.bgColor} ${tab.hoverBg} transition-all transform hover:scale-110 disabled:opacity-50 shadow-lg`}
                              title={`Mark as ${tab.label}`}
                            >
                              <tab.icon size={18} className="text-white" />
                            </button>
                          ))}
                      </div>

                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            handleMovieClick(movieId);
                          }}
                          className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-all transform hover:scale-110"
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
                          className="p-2 bg-red-500/80 rounded-lg hover:bg-red-600/80 transition-all transform hover:scale-110 disabled:opacity-50"
                          title="Remove from Watchlist"
                        >
                          <Trash2 size={18} className="text-white" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Updating overlay */}
                  {isUpdating && (
                    <div className="absolute inset-0 bg-black/80 flex items-center justify-center backdrop-blur-sm">
                      <div className="text-white text-sm font-medium animate-pulse">
                        Updating...
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-3 space-y-1">
                  <h4
                    className="text-white text-sm font-medium line-clamp-2 cursor-pointer hover:text-red-400 transition-colors"
                    onClick={() => handleMovieClick(movieId)}
                    title={movie.title}
                  >
                    {movie.title}
                  </h4>
                  <p className="text-gray-400 text-xs">
                    Added {new Date(item.created_at).toLocaleDateString()}
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
                key={item.id}
                className="flex gap-4 bg-gray-800/50 rounded-xl p-4 hover:bg-gray-800 transition-all cursor-pointer"
                onClick={() => handleMovieClick(movieId)}
              >
                <img
                  src={movie.poster_url || '/images/placeholder-movie.jpg'}
                  alt={movie.title}
                  className="w-20 h-30 object-cover rounded-lg"
                  onError={e => {
                    e.target.src = '/images/placeholder-movie.jpg';
                  }}
                />
                <div className="flex-1">
                  <h4 className="text-white font-medium hover:text-red-400 transition-colors">
                    {movie.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`px-2 py-1 rounded-lg text-xs font-medium ${currentTab.bgColor} text-white`}
                    >
                      <div className="flex items-center gap-1">
                        <currentTab.icon size={12} />
                        <span>{currentTab.label}</span>
                      </div>
                    </span>
                    {movie.rating && (
                      <div className="flex items-center gap-1 text-yellow-400 text-xs">
                        <span>★</span>
                        <span>{movie.rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                  <p className="text-gray-400 text-sm mt-1">
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {tabs
                    .filter(tab => tab.id !== item.status)
                    .map(tab => (
                      <button
                        key={tab.id}
                        onClick={e => {
                          e.stopPropagation();
                          handleStatusChange(watchlistId, movieId, tab.id);
                        }}
                        disabled={updatingIds.has(`${movieId}-${tab.id}`)}
                        className={`p-2 rounded-lg ${tab.bgColor} ${tab.hoverBg} transition-all disabled:opacity-50`}
                        title={`Mark as ${tab.label}`}
                      >
                        <tab.icon size={16} className="text-white" />
                      </button>
                    ))}
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      handleRemove(watchlistId, movieId);
                    }}
                    disabled={updatingIds.has(`${movieId}-remove`)}
                    className="p-2 bg-red-500 hover:bg-red-600 rounded-lg transition-all disabled:opacity-50"
                    title="Remove from Watchlist"
                  >
                    <Trash2 size={16} className="text-white" />
                  </button>
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
