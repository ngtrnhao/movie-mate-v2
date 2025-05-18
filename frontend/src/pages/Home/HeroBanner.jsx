const mockMovie = {
  title: 'The Shawshank Redemption',
  vote_average: 9.3,
  release_date: '1994-09-23',
  genres: ['Drama', 'Crime'],
  match: 94,
  overview:
    'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
};

const HeroBannerRecommendation = ({ movie = mockMovie }) => {
  const userRating = movie.vote_average ? Math.round(movie.vote_average / 2) : 0;

  return (
    <section className="relative flex min-h-[60vh] flex-col items-start justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-16">
      <div className="mx-auto ml-60 max-w-[1400px] px-4 text-left">
        {/* Genre */}
        <div className="mb-4 flex gap-2">
          <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white">
            Recommended
          </span>
          {movie.genres?.map((genre) => (
            <span
              key={genre}
              className="rounded-full bg-gray-700 px-3 py-1 text-xs font-medium text-gray-200"
            >
              {genre}
            </span>
          ))}
        </div>
        {/* Title */}
        <h1 className="mb-2 max-w-2xl break-words text-6xl font-bold text-white">{movie.title}</h1>
        {/* Rating,Year,Match */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex items-center">
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                className={`text-lg ${star <= userRating ? 'text-yellow ' : 'text-gray-400'}`}
              >
                ★
              </span>
            ))}
            <span className="ml-2 font-medium text-white">{userRating}/5</span>
          </div>
          <span className="text-gray-400">| {new Date(movie.release_date).getFullYear()}</span>
          {movie.match && (
            <span className="flex items-center font-semibold text-green-400">
              <svg className="mr-1 size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M5 13l4 4L19 7"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {movie.match}% match
            </span>
          )}
        </div>
        {/* Overview */}
        <p className="max-w-xl break-words text-lg font-medium text-gray-500">{movie.overview}</p>
        <div className="mt-6 flex flex-wrap gap-4">
          <button className="rounded-sm bg-red-600 px-6 py-2 font-semibold text-white transition hover:bg-red-700">
            View Details
          </button>
          <button className="hover:bg-via-white rounded-sm bg-white px-6 py-2 font-semibold text-black transition">
            Why Recommended?
          </button>
        </div>
      </div>
    </section>
  );
};
export default HeroBannerRecommendation;
