import { useState, useEffect } from 'react';
import { mockMovies } from '../../mocks/movies';
import { useNavigate } from 'react-router-dom';

const timeRanges = [
  { id: 'day', label: 'Today' },
  { id: 'week', label: 'This Week' },
  { id: 'month', label: 'This Month' },
];

const TrendingNow = () => {
  const [selectedRange, setSelectedRange] = useState('week');
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    setIsLoading(true);
    // Simulate API call with mock data
    setTimeout(() => {
      // Sort movies by rating and release date to simulate trending
      const sortedMovies = [...mockMovies]
        .sort((a, b) => {
          const ratingDiff = b.vote_average - a.vote_average;
          const dateDiff = new Date(b.release_date) - new Date(a.release_date);
          return ratingDiff || dateDiff;
        })
        .slice(0, 8);

      setTrendingMovies(sortedMovies);
      setIsLoading(false);
    }, 1000);
  }, [selectedRange]);

  return (
    <section className="w-full py-8">
      <div className="mx-auto max-w-4xl rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
        <h2 className="mb-1 flex items-center gap-2 text-2xl font-semibold text-white">
          <span className="text-blue-500">
            <svg
              viewBox="0 0 24 24"
              className="size-8"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          </span>
          Trending Now
        </h2>
        <p className="mb-6 text-sm text-gray-400">
          Discover what's popular and trending in the movie world
        </p>

        <div className="mb-6 flex justify-center gap-4">
          {timeRanges.map((range) => (
            <button
              key={range.id}
              onClick={() => setSelectedRange(range.id)}
              className={`rounded-lg border px-4 py-2 text-sm transition-all ${
                selectedRange === range.id
                  ? 'border-blue-500 bg-blue-500/10 text-blue-500'
                  : 'border-gray-700 bg-gray-800 text-white hover:border-blue-500/50'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="text-center text-gray-400">Loading trending movies...</div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {trendingMovies.map((movie) => (
              <div
                key={movie.id}
                className="group cursor-pointer overflow-hidden rounded-lg bg-gray-800"
              >
                <img
                  src={movie.poster_path}
                  alt={movie.title}
                  className="aspect-[2/3] w-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                <div className="p-2">
                  <h4 className="text-sm font-medium text-white">{movie.title}</h4>
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-xs text-yellow-500">★ {movie.vote_average}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(movie.release_date).getFullYear()}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {movie.genres.map((genre) => (
                      <span
                        key={genre}
                        className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-300"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 flex justify-center">
          <button
            onClick={() => navigate('/recommendation')}
            className="rounded border border-gray-300 bg-blue-600 px-6 py-2 font-semibold text-white transition hover:bg-blue-700"
          >
            View All Recommendation Tools
          </button>
        </div>
      </div>
    </section>
  );
};

export default TrendingNow;
