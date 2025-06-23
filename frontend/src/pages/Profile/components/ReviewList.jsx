import { CalendarToday, Star, ThumbUp } from '@mui/icons-material';
import { format } from 'date-fns';

const ReviewList = ({ reviews }) => {
  if (!reviews || reviews.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="mb-4 text-6xl text-gray-600">📝</div>
        <h3 className="mb-2 text-xl font-semibold text-gray-300">No Reviews Yet</h3>
        <p className="text-gray-400">Start reviewing movies to share your thoughts!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {reviews.map(review => (
        <div
          key={review.id}
          className="rounded-xl border border-gray-700 bg-gray-800/50 p-6 transition-all duration-200 hover:bg-gray-800/70"
        >
          <div className="mb-4 flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="size-12 overflow-hidden rounded-lg bg-gradient-to-br from-gray-700 to-gray-800 shadow-lg">
                {review.movie?.poster_path ? (
                  <img
                    src={review.movie.poster_path}
                    alt={review.movie?.title}
                    className="size-full object-cover"
                    onError={e => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div
                  className={`${review.movie?.poster_path ? 'hidden' : 'flex'} size-full items-center justify-center text-2xl`}
                  style={{ display: review.movie?.poster_path ? 'none' : 'flex' }}
                >
                  🎬
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-red-400">{review.movie?.title}</h4>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <CalendarToday fontSize="small" />
                  <span>
                    {review.created_at
                      ? format(new Date(review.created_at), 'MMM dd, yyyy')
                      : 'Recently'}
                  </span>
                </div>
              </div>
            </div>

            {review.rating && (
              <div className="flex items-center gap-1 rounded-full bg-yellow-500/20 px-3 py-1">
                <Star className="text-yellow-500" fontSize="small" />
                <span className="font-medium text-yellow-500">{review.rating}/10</span>
              </div>
            )}
          </div>

          <p className="mb-4 leading-relaxed text-gray-300">{review.content}</p>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-gray-400">
              {review.likes_count > 0 && (
                <div className="flex items-center gap-1">
                  <ThumbUp fontSize="small" />
                  <span>{review.likes_count} likes</span>
                </div>
              )}
            </div>

            <button className="rounded-lg px-3 py-1 text-sm text-gray-400 transition-colors hover:bg-gray-700 hover:text-white">
              Read More
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ReviewList;
