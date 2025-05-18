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
  trailer_url:
    'https://player.vimeo.com/external/371433846.sd.mp4?s=c27eecc69a27dbc4ff2b87d38afc35f1a9e7c02d&profile_id=164&oauth2_token_id=57447761',
};

const HeroBannerRecommendation = ({ movie = mockMovie }) => {
  const userRating = movie.vote_average ? Math.round(movie.vote_average / 2) : 0;

  return (
    <section className="relative min-h-[80vh] w-full">
      {/* Background Video */}
      <div className="absolute inset-0">
        <video autoPlay loop muted playsInline className="h-full w-full object-cover">
          <source src={movie.trailer_url} type="video/mp4" />
          {/* Fallback image if video fails to load */}
          <img src={movie.backdrop_path} alt={movie.title} className="h-full w-full object-cover" />
        </video>
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/70 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative mx-auto ml-60 flex h-full max-w-[1400px] items-center px-4">
        <div className="max-w-2xl">
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
          <h1 className="mb-2 max-w-2xl break-words text-6xl font-bold text-white">
            {movie.title}
          </h1>
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
          <p className="max-w-xl break-words text-lg font-medium text-gray-300">{movie.overview}</p>
          <div className="mt-6 flex flex-wrap gap-4">
            <button className="rounded-sm bg-red-600 px-6 py-2 font-semibold text-white transition hover:bg-red-700">
              View Details
            </button>
            <button className="hover:bg-via-white rounded-sm bg-white px-6 py-2 font-semibold text-black transition">
              Why Recommended?
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroBannerRecommendation;
