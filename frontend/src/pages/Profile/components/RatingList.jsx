import { Star, CalendarToday } from '@mui/icons-material';
import { format } from 'date-fns';

const RatingList = ({ ratings }) => {
  if (!ratings || ratings.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="mb-4 text-6xl text-gray-600">⭐</div>
        <h3 className="mb-2 text-xl font-semibold text-gray-300">No Ratings Yet</h3>
        <p className="text-gray-400">Start rating movies to track your preferences!</p>
      </div>
    );
  }

  const getRatingColor = rating => {
    if (rating >= 8) return 'text-green-400 bg-green-400/20 border-green-400/30';
    if (rating >= 6) return 'text-yellow-400 bg-yellow-400/20 border-yellow-400/30';
    return 'text-red-400 bg-red-400/20 border-red-400/30';
  };

  return (
    <div className="space-y-3 p-6">
      {ratings.map(rating => (
        <div
          key={rating.id}
          className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-800/50 p-4 transition-all duration-200 hover:bg-gray-800/70"
        >
          <div className="flex items-center gap-4">
            <div className="h-14 w-10 overflow-hidden rounded-lg bg-gradient-to-br from-gray-700 to-gray-800 shadow-lg">
              {rating.movie?.poster_path ? (
                <img
                  src={rating.movie.poster_path}
                  alt={rating.movie?.title}
                  className="size-full object-cover"
                  onError={e => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div
                className={`${rating.movie?.poster_path ? 'hidden' : 'flex'} size-full items-center justify-center text-lg`}
                style={{ display: rating.movie?.poster_path ? 'none' : 'flex' }}
              >
                🎬
              </div>
            </div>

            <div className="flex-1">
              <h4 className="font-semibold text-red-400">{rating.movie?.title}</h4>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <CalendarToday fontSize="small" />
                <span>
                  {rating.created_at
                    ? format(new Date(rating.created_at), 'MMM dd, yyyy')
                    : 'Recently'}
                </span>
              </div>
            </div>
          </div>

          <div
            className={`flex items-center gap-2 rounded-full border px-4 py-2 ${getRatingColor(rating.rating)}`}
          >
            <Star fontSize="small" />
            <span className="font-bold">{rating.rating}/10</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RatingList;
