import { useState, useEffect, useCallback } from 'react';
import MovieMateLogo from '../../components/Header/Logo';

const LandingPage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [featuredMovies, setFeaturedMovies] = useState([]);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [language, setLanguage] = useState('en-US'); // Default to English

  // TMDB Configuration
  const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
  const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';
  const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds

  const options = {
    method: 'GET',
    headers: {
      accept: 'application/json',
      Authorization:
        'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0YzMzOGUzYTMzNGI4ZjgxN2M0NWNlOGIwY2JhNmRmMSIsIm5iZiI6MTc0MDYwODk5Mi40MTkwMDAxLCJzdWIiOiI2N2JmOTVlMGJjNjkzNWEwMDFhMjM2MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iOVSJPSuTWhbnD5AAQBCnQ5TYXVLCwVOgPMytmB4rHs',
    },
  };

  const fetchMovies = useCallback(async () => {
    try {
      // Fetch trending movies with both languages
      const [enResponse, viResponse] = await Promise.all([
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=en-US`, options),
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=vi-VN`, options),
      ]);

      if (!enResponse.ok || !viResponse.ok) {
        throw new Error('Failed to fetch movies');
      }

      const [enData, viData] = await Promise.all([enResponse.json(), viResponse.json()]);

      // Get detailed information for each movie including videos
      const moviesWithDetails = await Promise.all(
        enData.results.slice(0, 3).map(async (enMovie, index) => {
          const viMovie = viData.results[index]; // Get corresponding Vietnamese data

          // Fetch detailed information in both languages
          const [enDetails] = await Promise.all([
            fetch(
              `${TMDB_BASE_URL}/movie/${enMovie.id}?language=en-US&append_to_response=videos`,
              options
            ).then((res) => res.json()),
            fetch(
              `${TMDB_BASE_URL}/movie/${enMovie.id}?language=vi-VN&append_to_response=videos`,
              options
            ).then((res) => res.json()),
          ]);

          return {
            id: enMovie.id,
            title: {
              en: enMovie.title,
              vi: viMovie.title,
            },
            year: new Date(enMovie.release_date).getFullYear(),
            rating: enMovie.vote_average.toFixed(1),
            description: {
              en: enMovie.overview,
              vi: viMovie.overview,
            },
            imageUrl: `${TMDB_IMAGE_BASE_URL}${enMovie.backdrop_path}`,
            trailerUrl: enDetails.videos?.results?.[0]?.key
              ? `https://www.youtube.com/watch?v=${enDetails.videos.results[0].key}`
              : null,
          };
        })
      );

      // Compare new movies with current ones
      const hasNewMovies =
        !featuredMovies.length ||
        moviesWithDetails.some(
          (newMovie) => !featuredMovies.find((currentMovie) => currentMovie.id === newMovie.id)
        );

      if (hasNewMovies) {
        // Preload images
        await Promise.all(
          moviesWithDetails.map((movie) => {
            return new Promise((resolve, reject) => {
              const img = new Image();
              img.src = movie.imageUrl;
              img.onload = resolve;
              img.onerror = reject;
            });
          })
        );

        setFeaturedMovies(moviesWithDetails);
        setLastUpdate(Date.now());
      }

      setIsLoading(false);
    } catch (err) {
      console.error('Error fetching movies:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [featuredMovies]);

  // Toggle language function
  const toggleLanguage = () => {
    setLanguage((prev) => (prev === 'en-US' ? 'vi-VN' : 'en-US'));
  };

  // Initial fetch
  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  // Auto-refresh movies
  useEffect(() => {
    const intervalId = setInterval(() => {
      const now = Date.now();
      if (now - lastUpdate >= REFRESH_INTERVAL) {
        fetchMovies();
      }
    }, REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [fetchMovies, lastUpdate]);

  // Slide show interval
  useEffect(() => {
    if (featuredMovies.length === 0) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % featuredMovies.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [featuredMovies.length]);

  if (error) {
    return (
      <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="text-center text-red-600">
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading || featuredMovies.length === 0) {
    return (
      <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  const currentMovie = featuredMovies[currentSlide];

  // Function to handle trailer click
  const handleTrailerClick = (trailerUrl) => {
    if (trailerUrl) {
      window.open(trailerUrl, '_blank');
    }
  };

  return (
    <div className="bg-background relative min-h-screen">
      {/* Navigation Header */}
      <header className="absolute inset-x-0 top-0 z-10">
        <div className="mx-auto max-w-[1400px] px-4">
          <div className="flex h-20 items-center justify-between">
            <MovieMateLogo />
            <div className="flex items-center gap-4">
              <button
                onClick={toggleLanguage}
                className="rounded-md border border-gray-600 px-4 py-2 text-white transition-colors hover:bg-white/10"
              >
                {language === 'en-US' ? 'VI' : 'EN'}
              </button>
              <button className="rounded-md border border-red-600 px-4 py-2 text-red-600 transition-colors hover:bg-red-600 hover:text-white">
                Sign In
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section with Slider */}
      <section className="relative min-h-screen">
        {/* Background Slides */}
        {featuredMovies.map((movie, index) => (
          <div
            key={movie.id}
            className={`absolute inset-0 transition-opacity duration-1000 ${
              index === currentSlide ? 'opacity-100' : 'opacity-0'
            }`}
          >
            {/* Background Image */}
            <div
              className="absolute inset-0 bg-cover bg-center"
              style={{ backgroundImage: `url(${movie.imageUrl})` }}
            />
            {/* Gradient Overlay */}
            <div className="from-background/80 via-background/50 to-background absolute inset-0 bg-gradient-to-b" />
          </div>
        ))}

        {/* Content */}
        <div className="relative mx-auto max-w-[1400px] px-4 pt-32">
          <div className="flex min-h-[calc(100vh-80px)] flex-col items-center justify-center text-center">
            {/* Main Title */}
            <h1 className="mb-6 text-6xl font-bold tracking-tight text-white">
              {language === 'en-US' ? (
                <>
                  Discover Your Next
                  <br />
                  Favorite <span className="text-red-600 dark:text-red-500">Movie</span>
                </>
              ) : (
                <>
                  Khám Phá
                  <br />
                  <span className="text-red-600 dark:text-red-500">Phim</span> Yêu Thích
                </>
              )}
            </h1>

            {/* Description */}
            <p className="mb-8 max-w-2xl text-lg text-gray-300">
              {currentMovie?.description?.[language === 'en-US' ? 'en' : 'vi']}
            </p>

            {/* CTA Buttons */}
            <div className="mb-16 flex gap-4">
              <button className="flex h-11 items-center justify-center rounded-md bg-red-600 px-8 text-sm font-medium text-white transition-colors hover:bg-red-700">
                {language === 'en-US' ? 'Explore Movies' : 'Khám Phá Phim'}
                <span className="ml-2">→</span>
              </button>
              <button className="flex h-11 items-center justify-center rounded-md border border-gray-600 px-8 text-sm font-medium text-white transition-colors hover:bg-white/10">
                {language === 'en-US' ? 'How It Works' : 'Hướng Dẫn'}
              </button>
            </div>

            {/* Featured Movie Info */}
            <div className="text-center">
              <p className="mb-4 text-sm uppercase tracking-wider text-gray-400">
                {language === 'en-US' ? 'NOW FEATURING' : 'ĐANG CHIẾU'}
              </p>
              <h2 className="mb-2 text-2xl font-bold text-white">
                {currentMovie?.title?.[language === 'en-US' ? 'en' : 'vi']}
              </h2>
              <div className="mb-4 flex items-center justify-center gap-2">
                <span className="text-yellow-500">★</span>
                <span className="font-medium text-white">{currentMovie?.rating}</span>
                <span className="text-gray-400">| {currentMovie?.year}</span>
              </div>
              <button
                onClick={() => handleTrailerClick(currentMovie?.trailerUrl)}
                className={`inline-flex items-center justify-center rounded-md border border-red-600 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-600 hover:text-white ${
                  !currentMovie?.trailerUrl ? 'cursor-not-allowed opacity-50' : ''
                }`}
                disabled={!currentMovie?.trailerUrl}
              >
                <span className="mr-2">▶</span>
                {language === 'en-US' ? 'Watch Trailer' : 'Xem Trailer'}
              </button>
            </div>

            {/* Scroll Indicator */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
              <svg
                className="size-6 text-gray-400"
                fill="none"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
          </div>
        </div>

        {/* Slide Navigation Dots */}
        <div className="absolute bottom-12 left-1/2 flex -translate-x-1/2 gap-2">
          {featuredMovies.map((movie, index) => (
            <button
              key={movie.id}
              onClick={() => setCurrentSlide(index)}
              className={`size-2 rounded-full transition-all ${
                index === currentSlide ? 'w-8 bg-red-600' : 'bg-gray-600 hover:bg-gray-500'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
