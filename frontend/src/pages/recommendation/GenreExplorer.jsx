import { useState } from 'react';
import { mockMovies } from '../../mocks/movies';
import { useNavigate } from 'react-router-dom';

const genres = [
  'Action',
  'Adventure',
  'Animation',
  'Comedy',
  'Crime',
  'Documentary',
  'Drama',
  'Family',
  'Fantasy',
  'Horror',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Thriller',
];

const GenreExplorer = () => {
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleGenreToggle = genre => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  const handleSearch = () => {
    if (selectedGenres.length === 0) return;

    setIsLoading(true);
    // Simulate API call with mock data
    setTimeout(() => {
      const genreMovies = mockMovies
        .filter(movie => selectedGenres.every(genre => movie.genres.includes(genre)))
        .slice(0, 8);

      setRecommendations(genreMovies);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <section className="w-full py-8">
      <div className="mx-auto max-w-4xl rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
        <h2 className="mb-1 flex items-center gap-2 text-2xl font-semibold text-white">
          <span className="text-green-500">
            <svg
              viewBox="0 0 24 24"
              className="size-8"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </span>
          Genre Explorer
        </h2>
        <p className="mb-6 text-sm text-gray-400">
          Select one or more genres to discover movies that match your interests
        </p>

        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
          {genres.map(genre => (
            <button
              key={genre}
              onClick={() => handleGenreToggle(genre)}
              className={`rounded-lg border p-2 text-sm transition-all ${
                selectedGenres.includes(genre)
                  ? 'border-green-500 bg-green-500/10 text-green-500'
                  : 'border-gray-700 bg-gray-800 text-white hover:border-green-500/50'
              }`}
            >
              {genre}
            </button>
          ))}
        </div>

        <div className="mb-6 flex justify-center">
          <button
            onClick={handleSearch}
            disabled={selectedGenres.length === 0}
            className={`rounded border px-6 py-2 font-semibold text-white transition ${
              selectedGenres.length === 0
                ? 'cursor-not-allowed border-gray-600 bg-gray-600'
                : 'border-green-500 bg-green-600 hover:bg-green-700'
            }`}
          >
            Find Movies
          </button>
        </div>

        {isLoading && (
          <div className="text-center text-gray-400">
            Searching for movies in your selected genres...
          </div>
        )}

        {recommendations.length > 0 && (
          <div>
            <h3 className="mb-4 text-xl font-semibold text-white">Recommended Movies</h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              {recommendations.map(movie => (
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
                      {movie.genres.map(genre => (
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
          </div>
        )}
      </div>
    </section>
  );
};

export default GenreExplorer;
