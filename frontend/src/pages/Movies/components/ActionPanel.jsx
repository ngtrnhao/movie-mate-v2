import { useState, useEffect } from 'react';
import { Plus, Heart, Share, Play } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useFavorites } from '../../../hooks/useFavorites';
import { useWatchlistContext } from '../../../context/WatchlistContext';
import useUserTracking from '../../../hooks/useUserTracking';
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

  const { trackFavorite, trackWatchlist } = useUserTracking();

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
      const wasInWatchlist = isInWatchlist(movieId);

      // ✅ Track watchlist action BEFORE the action
      trackWatchlist(movieId, !wasInWatchlist);
      if (wasInWatchlist) {
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

    const wasFavorited = isFavorited(movieId);

    // ✅ Track favorite action BEFORE the action
    trackFavorite(movieId, !wasFavorited);

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
    <div className="space-y-3 sm:space-y-5">
      {/* All Action Buttons - Responsive Layout */}
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
        {/* Trailer Button - Prominent but responsive */}
        {trailers.length > 0 && (
          <button
            onClick={handleWatchNow}
            className="group relative flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-red-600 via-red-500 to-pink-500 px-4 py-2 text-sm font-bold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:from-red-500 hover:to-pink-400 hover:shadow-xl sm:w-auto sm:gap-2 sm:px-5 sm:py-2.5 sm:text-sm"
          >
            <div className="flex size-5 items-center justify-center rounded-full bg-white/20 transition-all duration-300 group-hover:bg-white/30 sm:size-6">
              <Play className="ml-0.5 size-3 sm:size-4" fill="white" />
            </div>
            <span className="relative z-10 font-bold">{t('details.watchTrailer')}</span>
          </button>
        )}

        {/* Secondary Action Buttons - Responsive grid on mobile, flex on larger screens */}
        <div className="grid grid-cols-3 gap-1.5 sm:flex sm:flex-wrap sm:gap-2">
          {/* Add to Favorites */}
          <button
            onClick={handleToggleFavorite}
            disabled={isTogglingFavorite || favoritesLoading}
            className={`group flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 sm:px-3 sm:py-2 sm:text-xs ${
              isLiked ? 'text-pink-500 hover:text-pink-600' : 'text-white hover:text-red-500'
            }`}
          >
            <Heart
              fill={isLiked ? 'currentColor' : 'none'}
              className={`size-3 transition-transform duration-200 group-hover:scale-110 sm:size-5 ${
                isTogglingFavorite ? 'animate-pulse' : ''
              }`}
            />
            <span className="hidden sm:inline">
              {isTogglingFavorite
                ? isLiked
                  ? 'Removing...'
                  : 'Adding...'
                : t('details.addToFavorites')}
            </span>
            <span className="sm:hidden">
              {isTogglingFavorite ? (isLiked ? 'Removing...' : 'Adding...') : 'Favorites'}
            </span>
          </button>

          {/* Add to Watchlist */}
          <button
            onClick={handleToggleWatchlist}
            disabled={isTogglingWatchlist || watchlistLoading}
            className={`group flex items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 sm:px-3 sm:py-2 sm:text-xs ${
              isInList ? 'text-green-500 hover:text-green-600' : 'text-white hover:text-red-500'
            }`}
          >
            <Plus
              className={`transition-transform duration-200 group-hover:scale-110 sm:size-8
                isTogglingWatchlist ? 'animate-pulse' : ''
              } ${isInList ? 'rotate-45' : ''}`}
            />
            <span className="hidden sm:inline">
              {isTogglingWatchlist
                ? isInList
                  ? 'Removing...'
                  : 'Adding...'
                : isInList
                  ? 'Remove from Watchlist'
                  : t('details.addToWatchlist')}
            </span>
            <span className="sm:hidden">
              {isTogglingWatchlist
                ? isInList
                  ? 'Removing...'
                  : 'Adding...'
                : isInList
                  ? 'Remove'
                  : 'Watchlist'}
            </span>
          </button>

          {/* Share Button */}
          <button
            onClick={handleShare}
            className="group flex items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-white transition-all duration-200 hover:text-red-500 sm:px-3 sm:py-2"
          >
            <Share className="size-3 transition-transform duration-200 group-hover:scale-110 sm:size-4" />
            <span className="hidden sm:inline">{t('details.share')}</span>
            <span className="sm:hidden">Share</span>
          </button>
        </div>
      </div>

      {/* Error Message - Responsive text sizing */}
      {(actionError || favoritesError) && (
        <div className="mt-2 rounded-lg border border-red-500/20 bg-red-500/10 p-2 text-xs text-red-400 sm:mt-3 sm:text-sm">
          {actionError || favoritesError}
        </div>
      )}
    </div>
  );
};

export default ActionPanel;
