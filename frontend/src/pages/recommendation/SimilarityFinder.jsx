import { useState, useCallback } from 'react';
import { mockMovies } from '../../mocks/movies';
import { useNavigate } from 'react-router-dom';

const SimilarityFinder = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [similarMovies, setSimilarMovies] = useState([]);
  const navigate = useNavigate();

  // Search function with debounce
  const debouncedSearch = useCallback((query) => {
    const timeoutId = setTimeout(() => {
      if (query.length < 2) {
        setSearchResults([]);
        return;
      }

      const results = mockMovies.filter((movie) =>
        movie.title.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(results);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    // Simulate API call delay
    setTimeout(() => {
      const results = mockMovies.filter((movie) =>
        movie.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setSearchResults(results);
      setIsLoading(false);
    }, 500);
  };

  const handleMovieSelect = (movie) => {
    setSelectedMovie(movie);
    setSearchQuery(movie.title);
    setSearchResults([]);

    // Find similar movies based on genres and rating
    const similar = mockMovies
      .filter((m) => m.id !== movie.id)
      .sort((a, b) => {
        // Calculate similarity score based on genres and rating
        const genreMatchA = a.genres.filter((g) => movie.genres.includes(g)).length;
        const genreMatchB = b.genres.filter((g) => movie.genres.includes(g)).length;
        const ratingDiffA = Math.abs(a.vote_average - movie.vote_average);
        const ratingDiffB = Math.abs(b.vote_average - movie.vote_average);

        return genreMatchB - genreMatchA || ratingDiffA - ratingDiffB;
      })
      .slice(0, 4);

    setSimilarMovies(similar);
  };

  return (
    <section className="w-full py-8">
      <div className="mx-auto max-w-4xl rounded-lg border border-gray-800 bg-gray-900 p-6 shadow-lg">
        <h2 className="mb-1 flex items-center gap-2 text-2xl font-semibold text-white">
          <span className="text-red-600">
            <svg
              viewBox="0 0 24 24"
              className="size-8 text-red-600 transition-colors duration-150"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
              <path d="M7 2v20" />
              <path d="M17 2v20" />
              <path d="M2 12h20" />
              <path d="M2 7h5" />
              <path d="M2 17h5" />
              <path d="M17 17h5" />
              <path d="M17 7h5" />
            </svg>
          </span>
          Find Similar Movies
        </h2>
        <p className="mb-4 text-sm text-gray-400">
          Search for movies you love and we'll recommend similar titles you might enjoy
        </p>
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                debouncedSearch(e.target.value);
              }}
              placeholder="Enter a movie title..."
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-4 py-2 text-white placeholder:text-gray-400 focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
            />
            {/* Search Results Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute z-10 mt-1 w-full rounded-md border border-gray-700 bg-gray-800 shadow-lg">
                {searchResults.map((movie) => (
                  <button
                    key={movie.id}
                    onClick={() => handleMovieSelect(movie)}
                    className="flex w-full items-center gap-3 p-3 text-left text-white hover:bg-gray-700"
                  >
                    <img
                      src={movie.poster_path}
                      alt={movie.title}
                      className="size-12 rounded object-cover"
                    />
                    <div>
                      <h3 className="font-medium">{movie.title}</h3>
                      <p className="text-sm text-gray-400">
                        {new Date(movie.release_date).getFullYear()}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            type="submit"
            className="flex items-center rounded-md border border-gray-300 bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 focus:ring-offset-gray-900"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Selected Movie and Similar Movies */}
        {selectedMovie && (
          <div className="mt-6 space-y-6">
            {/* Selected Movie */}
            <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
              <div className="flex gap-4">
                <img
                  src={selectedMovie.poster_path}
                  alt={selectedMovie.title}
                  className="size-24 rounded object-cover"
                />
                <div>
                  <h3 className="text-xl font-semibold text-white">{selectedMovie.title}</h3>
                  <p className="mt-1 text-sm text-gray-400">{selectedMovie.overview}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedMovie.genres.map((genre) => (
                      <span
                        key={genre}
                        className="rounded-full bg-red-500/20 px-3 py-1 text-xs text-red-500"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Similar Movies */}
            {similarMovies.length > 0 && (
              <div>
                <h3 className="mb-4 text-lg font-semibold text-white">
                  Similar Movies You Might Like
                </h3>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {similarMovies.map((movie) => (
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
                        <div className="mt-1 text-xs text-gray-300">
                          <p className="line-clamp-2">{movie.overview}</p>
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
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};

export default SimilarityFinder;
