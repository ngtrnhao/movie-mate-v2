import { memo, useMemo } from 'react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const Rating = memo(({ rating, voteAverage, voteCount }) => {
  const { t } = useTranslation('movies');

  const mainRating = useMemo(() => {
    if (rating?.imdb && rating?.imdb_votes > 0) {
      return {
        value: rating.imdb,
        votes: rating.imdb_votes,
        source: 'IMDb',
      };
    }
    if (rating?.tmdb && rating?.tmdb_votes > 0) {
      return {
        value: rating.tmdb,
        votes: rating.tmdb_votes,
        source: 'TMDB',
      };
    }
    if (voteAverage && voteCount > 0) {
      return {
        value: voteAverage,
        votes: voteCount,
        source: 'TMDb',
      };
    }
    return null;
  }, [rating, voteAverage, voteCount]);

  const starRating = useMemo(() => {
    if (!mainRating?.value) return 0;
    // Convert from 10-star to 5-star scale for star display
    return Math.round(mainRating.value / 2);
  }, [mainRating]);

  const formattedVoteCount = useMemo(() => {
    const votes = mainRating?.votes;
    if (!votes) return '0';
    if (votes >= 1_000_000) return `${(votes / 1_000_000).toFixed(1)}M`;
    if (votes >= 1000) return `${(votes / 1000).toFixed(1)}K`;
    return votes.toString();
  }, [mainRating]);

  if (!mainRating) {
    return (
      <div className="mt-2 flex items-center gap-2 text-sm text-gray-500">
        <span>{t('rating.notRated')}</span>
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {/* Stars Display */}
      <div
        className="flex items-center gap-1"
        title={`${(mainRating.value / 2).toFixed(1)} / 5 stars`}
      >
        {[1, 2, 3, 4, 5].map(star => (
          <span
            key={star}
            className={`text-lg leading-none ${
              star <= starRating ? 'text-yellow-400' : 'text-gray-600'
            }`}
          >
            ★
          </span>
        ))}
      </div>

      {/* Rating inside Source Icon */}
      <div className="flex items-center gap-2">
        <div
          className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${
            mainRating.source === 'IMDb' ? 'bg-yellow-500 text-black' : 'bg-blue-500 text-white'
          }`}
          title={`${mainRating.source} Rating: ${mainRating.value.toFixed(1)}/10`}
        >
          <span>{mainRating.source}</span>
          <span className="font-bold">{mainRating.value.toFixed(1)}</span>
        </div>

        {/* Vote Count */}
        <span className="text-gray-400">({formattedVoteCount})</span>
      </div>
    </div>
  );
});

Rating.displayName = 'Rating';

export default Rating;
