import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const MovieCard = ({ movie, showCharacter = false, className = '' }) => {
  const navigate = useNavigate();
  const { t } = useTranslation('movies');

  const handleClick = () => {
    if (movie.id) {
      navigate(`/movies/${movie.id}`);
    }
  };

  const getDisplayTitle = () => {
    return movie.title || movie.title_en || movie.title_vi || t('details.unknownMovie');
  };

  const getDisplayPoster = () => {
    return movie.poster_url || 'https://placehold.co/600x400';
  };

  const getDisplayYear = () => {
    if (movie.release_date) {
      return new Date(movie.release_date).getFullYear();
    }
    return null;
  };

  const getDisplayCharacter = () => {
    if (!showCharacter) return null;

    if (movie.main_character) return movie.main_character;
    if (movie.character) return movie.character;
    if (movie.all_characters && movie.all_characters.length > 0) {
      return movie.all_characters[0];
    }
    return null;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`cursor-pointer rounded-lg bg-gray-700 p-4 transition-colors hover:bg-gray-600 ${className}`}
      onClick={handleClick}
    >
      <img
        src={getDisplayPoster()}
        alt={getDisplayTitle()}
        className="mb-3 h-40 w-full rounded-lg object-cover"
        onError={e => {
          e.target.src = 'https://placehold.co/600x400';
        }}
      />
      <h3 className="mb-1 text-sm font-semibold text-white line-clamp-2">{getDisplayTitle()}</h3>
      {getDisplayYear() && <p className="text-xs text-gray-400">{getDisplayYear()}</p>}
      {getDisplayCharacter() && (
        <p className="mt-1 text-xs text-yellow-400 line-clamp-1">
          {t('details.as')} {getDisplayCharacter()}
        </p>
      )}
    </motion.div>
  );
};

export default MovieCard;
