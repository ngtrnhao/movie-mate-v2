import { useTranslation } from '../../../i18n/hooks/useTranslation';

const Rating = ({ voteAverage, voteCount }) => {
  const { t } = useTranslation('movies');

  // Convert TMDB rating (1-10) to user rating (1-5)
  const convertToFiveStarRating = (rating) => {
    if (!rating) return 0;
    return Math.round((rating / 10) * 5);
  };

  const formatVoteCount = (count) => {
    if (count >= 1_000_000) {
      return `${(count / 1_000_000).toFixed(1)}M`;
    }
    if (count >= 1_000) {
      return `${(count / 1_000).toFixed(1)}K`;
    }
    return count.toString();
  };

  // Get rating description using i18n
  const getRatingDescription = (rating) => {
    switch (rating) {
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
  };

  const userRating = convertToFiveStarRating(voteAverage);

  return (
    <div className="mt-2 flex items-center gap-2">
      {/* Star Rating */}
      <div className="flex items-center gap-1">
        <div className="flex">
          {[1, 2, 3, 4, 5].map((star) => (
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
      {userRating > 0 && (
        <span className="text-sm text-gray-400">({getRatingDescription(userRating)})</span>
      )}

      {/* Vote Count */}
      {voteCount > 0 && (
        <span className="text-sm text-gray-400">
          ({formatVoteCount(voteCount)} {t('rating.votes')})
        </span>
      )}
    </div>
  );
};

export default Rating;
