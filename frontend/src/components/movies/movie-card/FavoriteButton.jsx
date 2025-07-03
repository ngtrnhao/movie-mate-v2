import { useState } from 'react';
import { Heart } from 'lucide-react';
import { useFavorites } from '../../../hooks/useFavorites';

const FavoriteButton = ({
  movie,
  size = 'sm',
  showText = false,
  className = '',
  variant = 'overlay' // 'overlay', 'solid', 'ghost'
}) => {
  const {
    isFavorited,
    toggleFavorite,
    loading,
    error,
    isAuthenticated
  } = useFavorites();

  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      // You might want to show a login modal here
      alert('Please login to add favorites');
      return;
    }

    if (isToggling) return;

    setIsToggling(true);
    await toggleFavorite(movie.id, movie);
    setIsToggling(false);
  };

  const isLiked = isFavorited(movie.id);

  // Size configurations
  const sizeConfig = {
    xs: { icon: 12, padding: 'p-1', text: 'text-xs' },
    sm: { icon: 16, padding: 'p-2', text: 'text-sm' },
    md: { icon: 20, padding: 'p-3', text: 'text-base' },
    lg: { icon: 24, padding: 'p-4', text: 'text-lg' }
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
    }`
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
      title={isLiked ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        size={config.icon}
        fill={isLiked ? 'currentColor' : 'none'}
        className={`
          transition-transform duration-200
          group-hover:scale-110
          ${isToggling ? 'animate-pulse' : ''}
        `}
      />
      {showText && (
        <span className={`${config.text} font-medium`}>
          {isToggling
            ? (isLiked ? 'Removing...' : 'Adding...')
            : (isLiked ? 'Favorited' : 'Favorite')
          }
        </span>
      )}
    </button>
  );
};

export default FavoriteButton;
