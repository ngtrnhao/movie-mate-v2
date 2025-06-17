import { memo, useMemo } from 'react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const Rating = memo(({ rating, voteAverage, voteCount }) => {
  const { t } = useTranslation('movies');

  // Memoize computed values
  const highestRating = useMemo(() => {
    if (rating?.imdb) return { value: rating.imdb, source: 'IMDB' };
    if (rating?.tmdb) return { value: rating.tmdb, source: 'TMDB' };
    if (rating?.rotten_tomatoes)
      return { value: rating.rotten_tomatoes, source: 'Rotten Tomatoes' };
    if (voteAverage) return { value: voteAverage, source: 'Average' };
    return null;
  }, [rating, voteAverage]);

  const userRating = useMemo(() => {
    if (!highestRating) return 0;
    return Math.round((highestRating.value / 10) * 5);
  }, [highestRating]);

  const totalVotes = useMemo(() => {
    return voteCount || rating?.imdb_votes || 0;
  }, [voteCount, rating?.imdb_votes]);

  const formattedVoteCount = useMemo(() => {
    if (!totalVotes) return '0';
    if (totalVotes >= 1_000_000) {
      return `${(totalVotes / 1_000_000).toFixed(1)}M`;
    }
    if (totalVotes >= 1_000) {
      return `${(totalVotes / 1_000).toFixed(1)}K`;
    }
    return totalVotes.toString();
  }, [totalVotes]);

  const ratingDescription = useMemo(() => {
    switch (userRating) {
      case 1:
        return t('rating.veryBad');
      case 2:
        return t('rating.bad');
      case 3:
        return t('rating.average');
      case 4:
        return t('rating.good');
      case 5:
        return t('rating.excellent');
      default:
        return t('rating.notRated');
    }
  }, [userRating, t]);

  return (
    <div className="mt-2 flex items-center gap-2">
      {/* Star Rating */}
      <div className="flex items-center gap-1">
        <div className="flex">
          {[1, 2, 3, 4, 5].map(star => (
            <span
              key={star}
              className={`text-lg ${star <= userRating ? 'text-yellow-400' : 'text-gray-400'}`}
            >
              ★
            </span>
          ))}
        </div>
        <span className="ml-1 font-medium text-white">
          {userRating > 0 ? `${userRating}/5` : 'N/A'}
        </span>
      </div>

      {/* Rating Description */}
      {userRating > 0 && <span className="text-sm text-gray-400">({ratingDescription})</span>}

      {/* Vote Count and Source */}
      {totalVotes > 0 && (
        <span className="text-sm text-gray-400">
          ({formattedVoteCount} {t('rating.votes')} - {highestRating?.source})
        </span>
      )}
    </div>
  );
});

Rating.displayName = 'Rating';

export default Rating;
