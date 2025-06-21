import { memo, useMemo } from 'react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const Rating = memo(({ rating, voteAverage, voteCount }) => {
  const { t } = useTranslation('movies');

  const mainRating = useMemo(() => {
    if (rating?.tmdb && rating?.tmdb_votes > 0) {
      return {
        value: rating.tmdb,
        votes: rating.tmdb_votes,
        source: 'TMDB',
      };
    }
    if (rating?.imdb && rating?.imdb_votes > 0) {
      return {
        value: rating.imdb,
        votes: rating.imdb_votes,
        source: 'IMDb',
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
      <div className="flex items-center gap-1" title={`${mainRating.value.toFixed(1)} / 10`}>
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
      <div className="flex items-center gap-2 text-gray-400">
        <span className="font-bold text-white">{mainRating.value.toFixed(1)}</span>
        <span>({formattedVoteCount})</span>
        <span
          className={`rounded-md px-1.5 py-0.5 text-xs font-semibold ${
            mainRating.source === 'IMDb'
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-blue-500/20 text-blue-400'
          }`}
        >
          {mainRating.source}
        </span>
      </div>
    </div>
  );
});

Rating.displayName = 'Rating';

export default Rating;
