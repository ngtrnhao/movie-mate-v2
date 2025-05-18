const mockMovie = {
  title: 'The Shawshank Redemption',
  vote_average: 9.3,
  release_date: '1994-09-23',
  genres: ['Drama', 'Crime'],
  match: 94,
  overview:
    'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
  poster_path: 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
  backdrop_path: 'https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg',
  trailer_url: 'https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4',
};

const HeroBannerRecommendation = ({ movie = mockMovie }) => {
  const userRating = movie.vote_average ? Math.round(movie.vote_average / 2) : 0;

  return (
    <section className="relative min-h-[105vh] w-full">
      {/* Background Video */}
      <div className="absolute inset-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="size-full object-cover"
          poster={movie.backdrop_path}
        >
          <source src={movie.trailer_url} type="video/mp4" />
          {/* Fallback image if video fails to load */}
          <img src={movie.backdrop_path} alt={movie.title} className="size-full object-cover" />
        </video>
        {/* Enhanced Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/40 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/60" />
      </div>

      {/* Content */}
      <div className="relative ml-14  flex h-full max-w-[1400px] items-center">
        <div className="mt-60 max-w-2xl">
          {/* Genre */}
          <div className="mb-4 flex gap-2">
            <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white shadow-lg">
              Recommended
            </span>
            {movie.genres?.map((genre) => (
              <span
                key={genre}
                className="rounded-full bg-gray-800/80 px-3 py-1 text-xs font-medium text-white shadow-lg backdrop-blur-sm"
              >
                {genre}
              </span>
            ))}
          </div>
          {/* Title */}
          <h1 className="mb-2 max-w-2xl break-words text-6xl font-bold text-white drop-shadow-lg">
            {movie.title}
          </h1>
          {/* Rating,Year,Match */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex items-center">
              {[1, 2, 3, 4, 5].map((star) => (
                <span
                  key={star}
                  className={`text-lg ${star <= userRating ? 'text-yellow-400' : 'text-gray-400'}`}
                >
                  ★
                </span>
              ))}
              <span className="ml-2 font-medium text-white drop-shadow-md">{userRating}/5</span>
            </div>
            <span className="text-gray-300 drop-shadow-md">
              | {new Date(movie.release_date).getFullYear()}
            </span>
            {movie.match && (
              <span className="flex items-center font-semibold text-green-400 drop-shadow-md">
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
          <p className="max-w-xl break-words text-lg font-medium text-gray-200 drop-shadow-md">
            {movie.overview}
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <button className="rounded-sm bg-red-600 px-6 py-2 font-semibold text-white shadow-lg transition hover:bg-red-700">
              View Details
            </button>
            <button className="rounded-sm bg-white/10 px-6 py-2 font-semibold text-white shadow-lg backdrop-blur-sm transition hover:bg-white/20">
              Why Recommended?
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroBannerRecommendation;
