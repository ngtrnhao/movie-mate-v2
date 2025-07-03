import { useState } from 'react';
import { Plus, Heart, Share, Play } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useFavorites } from '../../../hooks/useFavorites';
import { useWatchlistContext } from '../../../context/WatchlistContext';

const ActionPanel = ({ movie, onTrailerClick }) => {
  const { t } = useTranslation('movies');

  // Use our custom hooks
  const {
    isFavorited,
    toggleFavorite,
    loading: favoritesLoading,
    error: favoritesError,
    clearError: clearFavoritesError,
  } = useFavorites();

  const {
    openExistingModal,
    isInWatchlist,
    handleRemoveFromWatchlist,
    loading: watchlistLoading,
    watchlists,
  } = useWatchlistContext();

  // Local state for UI feedback
  const [isTogglingFavorite, setIsTogglingFavorite] = useState(false);
  const [isTogglingWatchlist, setIsTogglingWatchlist] = useState(false);
  const [actionError, setActionError] = useState(null);

  if (!movie) return null;

  const trailers = movie.trailers || [];

  const handleToggleWatchlist = async () => {
    if (isTogglingWatchlist) return;

    setIsTogglingWatchlist(true);
    setActionError(null);

    try {
      const movieId = parseInt(movie.id);
      if (isInWatchlist(movieId)) {
        // Find the watchlist that contains this movie
        const watchlistWithMovie = watchlists.find(list =>
          list.items.some(item => (item.movie_data?.id || item.movie?.id) === movieId)
        );

        if (watchlistWithMovie) {
          await handleRemoveFromWatchlist(watchlistWithMovie.id, movieId);
        }
      } else {
        // Show modal with existing watchlists
        openExistingModal(movieId, movie, window.location.pathname);
      }
    } catch (error) {
      setActionError('Failed to manage watchlist');
    } finally {
      setIsTogglingWatchlist(false);
    }
  };

  const handleToggleFavorite = async () => {
    if (isTogglingFavorite) return;

    setIsTogglingFavorite(true);
    setActionError(null);
    clearFavoritesError();

    // Ensure movieId is a number
    const movieId = parseInt(movie.id);
    if (isNaN(movieId)) {
      setActionError('Invalid movie ID');
      setIsTogglingFavorite(false);
      return;
    }

    const result = await toggleFavorite(movieId, movie);
    if (!result.success) {
      setActionError(`Favorites: ${result.error}`);
    }

    setIsTogglingFavorite(false);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: movie.title,
        text: `Check out ${movie.title}`,
        url: window.location.href,
      });
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  const handleWatchNow = () => {
    if (onTrailerClick) {
      onTrailerClick(movie);
    }
  };

  // Check current states
  const movieId = parseInt(movie.id);
  const isLiked = isFavorited(movieId);
  const isInList = isInWatchlist(movieId);

  return (
    <div className="space-y-6">
      {/* All Action Buttons in One Row */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Trailer Button - Prominent but in same row */}
        {trailers.length > 0 && (
          <button
            onClick={handleWatchNow}
            className="group relative flex items-center gap-3 rounded-full bg-gradient-to-r from-red-600 via-red-500 to-pink-500 px-6 py-3 text-base font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:from-red-500 hover:to-pink-400 hover:shadow-xl"
          >
            <div className="flex size-8 items-center justify-center rounded-full bg-white/20 transition-all duration-300 group-hover:bg-white/30">
              <Play size={18} fill="white" className="ml-0.5" />
            </div>
            <span className="relative z-10 font-bold">{t('details.watchTrailer')}</span>
          </button>
        )}

        {/* Add to Favorites */}
        <button
          onClick={handleToggleFavorite}
          disabled={isTogglingFavorite || favoritesLoading}
          className={`group flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
            isLiked ? 'text-pink-500 hover:text-pink-600' : 'text-white hover:text-red-500'
          }`}
        >
          <Heart
            size={16}
            fill={isLiked ? 'currentColor' : 'none'}
            className={`transition-transform duration-200 group-hover:scale-110 ${
              isTogglingFavorite ? 'animate-pulse' : ''
            }`}
          />
          <span>
            {isTogglingFavorite
              ? isLiked
                ? 'Removing...'
                : 'Adding...'
              : t('details.addToFavorites')}
          </span>
        </button>

        {/* Add to Watchlist */}
        <button
          onClick={handleToggleWatchlist}
          disabled={isTogglingWatchlist || watchlistLoading}
          className={`group flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
            isInList ? 'text-green-500 hover:text-green-600' : 'text-white hover:text-red-500'
          }`}
        >
          <Plus
            size={16}
            className={`transition-transform duration-200 group-hover:scale-110 ${
              isTogglingWatchlist ? 'animate-pulse' : ''
            } ${isInList ? 'rotate-45' : ''}`}
          />
          <span>
            {isTogglingWatchlist
              ? isInList
                ? 'Removing...'
                : 'Adding...'
              : t('details.addToWatchlist')}
          </span>
        </button>

        {/* Share Button */}
        <button
          onClick={handleShare}
          className="group flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-white transition-all duration-200 hover:text-red-500"
        >
          <Share size={16} className="transition-transform duration-200 group-hover:scale-110" />
          <span>{t('details.share')}</span>
        </button>
      </div>

      {/* Error Message */}
      {(actionError || favoritesError) && (
        <div className="mt-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          {actionError || favoritesError}
        </div>
      )}
    </div>
  );
};

export default ActionPanel;
