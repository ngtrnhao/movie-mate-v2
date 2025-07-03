import { useState } from 'react';
import { Plus, Check } from 'lucide-react';
import { useWatchlist } from '../../../hooks/useWatchlist';

const WatchlistButton = ({
  movie,
  size = 'sm',
  showText = false,
  className = '',
  variant = 'overlay', // 'overlay', 'solid', 'ghost'
}) => {
  const { isInWatchlist, toggleWatchlist, getWatchlistStatus, loading, error, isAuthenticated } =
    useWatchlist();

  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async e => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      alert('Please login to manage watchlist');
      return;
    }

    if (isToggling) return;

    setIsToggling(true);
    await toggleWatchlist(movie.id, movie);
    setIsToggling(false);
  };

  const isInList = isInWatchlist(movie.id);
  const status = getWatchlistStatus(movie.id);

  // Size configurations
  const sizeConfig = {
    xs: { icon: 12, padding: 'p-1', text: 'text-xs' },
    sm: { icon: 16, padding: 'p-2', text: 'text-sm' },
    md: { icon: 20, padding: 'p-3', text: 'text-base' },
    lg: { icon: 24, padding: 'p-4', text: 'text-lg' },
  };

  const config = sizeConfig[size] || sizeConfig.sm;

  // Variant styles
  const variantStyles = {
    overlay: `absolute top-2 left-2 ${config.padding} rounded-full backdrop-blur-sm transition-all duration-200 ${
      isInList
        ? 'bg-green-500/90 text-white hover:bg-green-600/90'
        : 'bg-black/50 text-white hover:bg-black/70'
    }`,
    solid: `${config.padding} rounded-lg transition-all duration-200 ${
      isInList
        ? 'bg-green-500 text-white hover:bg-green-600'
        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
    }`,
    ghost: `${config.padding} rounded-lg transition-all duration-200 ${
      isInList
        ? 'text-green-500 hover:text-green-600 hover:bg-green-50'
        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
    }`,
  };

  // Status text mapping
  const statusText = {
    PLANNED: 'Plan to Watch',
    WATCHING: 'Watching',
    WATCHED: 'Watched',
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isToggling || loading}
      className={`
        group flex items-center gap-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${className}
      `}
      title={isInList ? `Remove from watchlist (${statusText[status]})` : 'Add to watchlist'}
    >
      {isInList ? (
        <Check
          size={config.icon}
          className={`
            transition-transform duration-200
            group-hover:scale-110
            ${isToggling ? 'animate-pulse' : ''}
          `}
        />
      ) : (
        <Plus
          size={config.icon}
          className={`
            transition-transform duration-200
            group-hover:scale-110
            ${isToggling ? 'animate-pulse' : ''}
          `}
        />
      )}
      {showText && (
        <span className={`${config.text} font-medium`}>
          {isToggling
            ? isInList
              ? 'Removing...'
              : 'Adding...'
            : isInList
              ? statusText[status] || 'In Watchlist'
              : 'Watchlist'}
        </span>
      )}
    </button>
  );
};

export default WatchlistButton;
