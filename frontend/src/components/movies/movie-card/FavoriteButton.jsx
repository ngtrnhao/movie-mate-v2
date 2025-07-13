import { Heart } from 'lucide-react';
import { useSelector } from 'react-redux';
import { useFavoritesState } from '../../../hooks/useFavoritesState';
import { useFavoritesActions } from '../../../hooks/useFavoritesActions';
import { useUserLimits } from '../../../hooks/useUserLimits';
import useUserTracking from '../../../hooks/useUserTracking';
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
  const { trackFavorite } = useUserTracking();

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

    const isCurrentlyFavorited = isFavorited(movie.id);

    // Track favorite action
    trackFavorite(movie.id, !isCurrentlyFavorited);

    // Check if user can add more favorites
    if (!isCurrentlyFavorited && !canPerformAction('add_favorite')) {
      const message = getUpgradeMessage('favorites');
      toast.error(message);
      return;
    }

    // Toggle favorite logic
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

  const config = sizeConfig[size];

  // Variant configurations
  const getVariantClasses = () => {
    const baseClasses = `focus-ring inline-flex items-center gap-2 rounded transition-all duration-200 ${config.padding}`;

    if (variant === 'overlay') {
      return isLiked
        ? `${baseClasses} bg-red-600/90 text-white hover:bg-red-700/90`
        : `${baseClasses} bg-black/50 text-white hover:bg-red-600/90`;
    }

    if (variant === 'solid') {
      return isLiked
        ? `${baseClasses} bg-red-600 text-white hover:bg-red-700`
        : `${baseClasses} bg-gray-600 text-white hover:bg-red-600`;
    }

    // ghost variant
    return isLiked
      ? `${baseClasses} text-red-500 hover:text-red-400`
      : `${baseClasses} text-gray-400 hover:text-red-500`;
  };

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`${getVariantClasses()} ${className} ${loading ? 'cursor-not-allowed opacity-50' : ''}`}
      title={isLiked ? 'Remove from favorites' : 'Add to favorites'}
      type="button"
    >
      <Heart
        size={config.icon}
        fill={isLiked ? 'currentColor' : 'none'}
        className={loading ? 'animate-pulse' : ''}
      />
      {showText && (
        <span className={config.text}>
          {loading ? 'Loading...' : isLiked ? 'Favorited' : 'Favorite'}
        </span>
      )}
    </button>
  );
};

export default FavoriteButton;
