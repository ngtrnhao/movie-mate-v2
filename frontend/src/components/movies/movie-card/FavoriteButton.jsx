import { Heart } from 'lucide-react';
import { useSelector } from 'react-redux';
import { useFavoritesState } from '../../../hooks/useFavoritesState';
import { useFavoritesActions } from '../../../hooks/useFavoritesActions';
import { useUserLimits } from '../../../hooks/useUserLimits';
import { toast } from 'react-toastify';

const FavoriteButton = ({
  movie,
  size = 'sm',
  showText = false,
  className = '',
  variant = 'overlay', // 'overlay', 'solid', 'ghost'
}) => {
  const { isFavorited, loading: globalLoading, error } = useFavoritesState();
  const { addToFavorites, removeFromFavorites } = useFavoritesActions();

  // Get authentication status from Redux
  const { isAuthenticated } = useSelector(state => state.auth);

  const { canPerformAction, getUpgradeMessage, shouldShowUpgrade } = useUserLimits();

  const handleToggle = async e => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      toast.error('Please login to add favorites');
      return;
    }

    // Check if user can add more favorites
    if (!isFavorited(movie.id) && !canPerformAction('add_favorite')) {
      const message = getUpgradeMessage('favorites');
      toast.error(message);
      return;
    }

    // Toggle favorite logic
    const isCurrentlyFavorited = isFavorited(movie.id);
    const result = isCurrentlyFavorited
      ? await removeFromFavorites(movie.id)
      : await addToFavorites(movie.id, movie);

    // Show upgrade message if limit exceeded
    if (!result.success && shouldShowUpgrade('add_favorite')) {
      toast.error(getUpgradeMessage('favorites'));
    }
  };

  const isLiked = isFavorited(movie.id);
  const loading = globalLoading;

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
    overlay: `absolute top-2 right-2 ${config.padding} rounded-full backdrop-blur-sm transition-all duration-200 ${
      isLiked
        ? 'bg-pink-500/90 text-white hover:bg-pink-600/90'
        : 'bg-black/50 text-white hover:bg-black/70'
    }`,
    solid: `${config.padding} rounded-lg transition-all duration-200 ${
      isLiked
        ? 'bg-pink-500 text-white hover:bg-pink-600'
        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
    }`,
    ghost: `${config.padding} rounded-lg transition-all duration-200 ${
      isLiked
        ? 'text-pink-500 hover:text-pink-600 hover:bg-pink-50'
        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
    }`,
  };

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`
        group flex items-center gap-2
        disabled:opacity-70 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${className}
        ${loading ? 'animate-pulse' : ''}
      `}
      title={isLiked ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        size={config.icon}
        fill={isLiked ? 'currentColor' : 'none'}
        className={`
          transition-all duration-200
          group-hover:scale-110
          ${loading ? 'animate-bounce' : ''}
          ${error ? 'text-red-500' : ''}
        `}
      />
      {showText && (
        <span className={`${config.text} whitespace-nowrap font-medium`}>
          {loading ? (isLiked ? 'Removing...' : 'Adding...') : isLiked ? 'Favorited' : 'Favorite'}
        </span>
      )}
    </button>
  );
};

export default FavoriteButton;
