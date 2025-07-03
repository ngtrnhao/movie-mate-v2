import { useState, useEffect } from 'react';
import { Plus, Heart, Share, Play } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useFavorites } from '../../../hooks/useFavorites';
import { useWatchlist } from '../../../hooks/useWatchlist';

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
    isInWatchlist,
    toggleWatchlist,
    loading: watchlistLoading,
    error: watchlistError,
    clearError: clearWatchlistError,
  } = useWatchlist();

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
    clearWatchlistError();

    const result = await toggleWatchlist(movie.id, movie);

    if (!result.success) {
      setActionError(`Watchlist: ${result.error}`);
    }

    setIsTogglingWatchlist(false);
  };

  const handleToggleFavorite = async () => {
    if (isTogglingFavorite) return;

    setIsTogglingFavorite(true);
    setActionError(null);
    clearFavoritesError();

    console.log('🎬 ActionPanel: Toggle favorite clicked', {
      movieId: movie.id,
      movieIdType: typeof movie.id,
      movieTitle: movie.title,
      isCurrentlyFavorited: isFavorited(movie.id),
    });

    // Ensure movieId is a number
    const movieId = parseInt(movie.id);
    if (isNaN(movieId)) {
      console.error('❌ Invalid movie ID:', movie.id);
      setActionError('Invalid movie ID');
      setIsTogglingFavorite(false);
      return;
    }

    const result = await toggleFavorite(movieId, movie);
    console.log('🎬 ActionPanel: Toggle favorite result', result);

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

  const getTrailerUrl = () => {
    if (!trailers || trailers.length === 0) return null;

    // Tìm trailer có type là 'TRAILER' hoặc lấy trailer đầu tiên
    const trailer = trailers.find(t => t.type === 'TRAILER') || trailers[0];

    if (!trailer?.youtube_key) return null;

    return `https://www.youtube.com/watch?v=${trailer.youtube_key}`;
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

        {/* Comment Button */}
        <button className="group flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-white transition-all duration-200 hover:text-red-500">
          <svg
            className="size-4 transition-transform duration-200 group-hover:scale-110"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span>{t('details.comment')}</span>
        </button>
      </div>

      {/* Error Messages */}
      {(actionError || favoritesError || watchlistError) && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          {actionError && <div>{actionError}</div>}
          {favoritesError && <div>Favorites Error: {favoritesError}</div>}
          {watchlistError && <div>Watchlist Error: {watchlistError}</div>}
        </div>
      )}
    </div>
  );
};

export default ActionPanel;
