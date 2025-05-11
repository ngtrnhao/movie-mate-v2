import { useState, useEffect, useCallback, useRef } from 'react';
import MovieMateLogo from '../../components/header/Logo';
import { motion, AnimatePresence } from 'framer-motion';
import TabGroup from '../../components/movies/tab-group';
import MovieGrid from '../../components/movies/movie-grid/MovieGrid';
import CategoryGrid from '../../components/categories/CategoryGrid';
import { useCategories } from '../../hooks/useCategories';
import PlanList from '../../components/plans/PlanList';
import { CheckCircle } from 'lucide-react';
const TABS = [
  { key: 'trending', label: 'Trending' },
  { key: 'topRated', label: 'Top Rated' },
  { key: 'upcoming', label: 'Upcoming' },
];
const features = [
  'Explore a vast and diverse movie library',
  'Personalized movie recommendations',
  'Create and manage your watchlist',
  'Read and write movie reviews',
];
// const TabGroup = ({ tabs, activeTab, onTabChange }) => (
//   <div className="mb-8 flex justify-center gap-2" role="tablist">
//     {tabs.map((tab) => (
//       <button
//         key={tab.key}
//         role="tab"
//         aria-selected={activeTab === tab.key}
//         tabIndex={activeTab === tab.key ? 0 : -1}
//         onClick={() => onTabChange(tab.key)}
//         className={`rounded px-2 py-1 font-sans transition-colors
//           ${
//             activeTab === tab.key
//               ? 'bg-red-600 font-semibold text-white shadow'
//               : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700 hover:text-white'
//           }
//         `}
//       >
//         {tab.label}
//       </button>
//     ))}
//   </div>
// );

const LandingPage = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [featuredMovies, setFeaturedMovies] = useState([]);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [language, setLanguage] = useState('en-US'); // Default to English
  const [isPaused, setIsPaused] = useState(false); // Track if slideshow is paused
  const pauseTimeoutRef = useRef(null); // Reference to timeout for resuming slideshow
  const howItWorksRef = useRef(null);
  const [activeTab, setActiveTab] = useState(TABS[0].key);

  // New state for tab-based movies
  const [moviesByTab, setMoviesByTab] = useState({
    trending: [],
    topRated: [],
    upcoming: [],
  });
  const [tabLoading, setTabLoading] = useState(false);
  const [tabError, setTabError] = useState(null);

  // TMDB Configuration
  const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
  const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';
  const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds
  const SLIDE_INTERVAL = 3000; // 5 seconds between slides
  const PAUSE_DURATION = 5000; // 15 seconds pause after user interaction

  const options = {
    method: 'GET',
    headers: {
      accept: 'application/json',
      Authorization:
        'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0YzMzOGUzYTMzNGI4ZjgxN2M0NWNlOGIwY2JhNmRmMSIsIm5iZiI6MTc0MDYwODk5Mi40MTkwMDAxLCJzdWIiOiI2N2JmOTVlMGJjNjkzNWEwMDFhMjM2MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iOVSJPSuTWhbnD5AAQBCnQ5TYXVLCwVOgPMytmB4rHs',
    },
  };

  const { data: categories, isLoading: catLoading, error: catError } = useCategories();

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

  // New function for tab-based movie fetching
  const fetchMoviesByTab = useCallback(async (tabKey) => {
    setTabLoading(true);
    setTabError(null);
    let url = '';
    if (tabKey === 'trending') url = `${TMDB_BASE_URL}/trending/movie/week`;
    if (tabKey === 'topRated') url = `${TMDB_BASE_URL}/movie/top_rated`;
    if (tabKey === 'upcoming') url = `${TMDB_BASE_URL}/movie/upcoming`;

    try {
      // Fetch movies in both languages
      const [enResponse, viResponse] = await Promise.all([
        fetch(`${url}?language=en-US`, options),
        fetch(`${url}?language=vi-VN`, options),
      ]);

      if (!enResponse.ok || !viResponse.ok) {
        throw new Error('Failed to fetch movies');
      }

      const [enData, viData] = await Promise.all([enResponse.json(), viResponse.json()]);

      // Combine and prioritize Vietnamese movies
      const combinedMovies = [...(viData.results || []), ...(enData.results || [])];

      // Remove duplicates based on movie ID, keeping Vietnamese version if available
      const uniqueMovies = combinedMovies.reduce((acc, movie) => {
        if (!acc.find((m) => m.id === movie.id)) {
          acc.push(movie);
        }
        return acc;
      }, []);

      setMoviesByTab((prev) => ({ ...prev, [tabKey]: uniqueMovies }));
    } catch (err) {
      setTabError('Failed to fetch movies');
      console.error('Error fetching movies:', err);
    }
    setTabLoading(false);
  }, []);

  // Fetch movies for active tab
  useEffect(() => {
    if (moviesByTab[activeTab].length === 0) {
      fetchMoviesByTab(activeTab);
    }
  }, [activeTab, fetchMoviesByTab, moviesByTab]);

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
  }, [fetchMovies, lastUpdate, REFRESH_INTERVAL]);

  // Slide show interval with pause functionality
  useEffect(() => {
    if (featuredMovies.length === 0) return;

    // Only set interval if not paused
    if (!isPaused) {
      const interval = setInterval(() => {
        setCurrentSlide((prev) => (prev + 1) % featuredMovies.length);
      }, SLIDE_INTERVAL);

      return () => clearInterval(interval);
    }
  }, [featuredMovies.length, isPaused]);

  // Function to handle user interaction with slides
  const handleSlideInteraction = (index) => {
    // Clear any existing timeout
    if (pauseTimeoutRef.current) {
      clearTimeout(pauseTimeoutRef.current);
    }

    // Set the current slide
    setCurrentSlide(index);

    // Pause the slideshow
    setIsPaused(true);

    // Resume slideshow after pause duration
    pauseTimeoutRef.current = setTimeout(() => {
      setIsPaused(false);
    }, PAUSE_DURATION);
  };

  const scrollToHowItWorks = () => {
    howItWorksRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-red-600">
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading || featuredMovies.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
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
    <div className="relative min-h-screen bg-gray-900">
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
      <section className="relative min-h-screen overflow-hidden">
        {/* Background Slides */}
        <AnimatePresence mode="wait">
          {featuredMovies.map((movie, index) => (
            <motion.div
              key={movie.id}
              initial={{ opacity: 0, scal: 1.1 }}
              animate={{
                opacity: index === currentSlide ? 1 : 0,
                scale: index === currentSlide ? 1 : 1.1,
              }}
              exit={{ opacity: 0, scale: 1.1 }}
              transition={{ duration: 0.8, ease: 'easeInOut' }}
              className="absolute inset-0"
            >
              {/* Background Image */}
              <div
                className="absolute inset-0 bg-cover bg-center"
                style={{ backgroundImage: `url(${movie.imageUrl})` }}
              />
              {/* Gradient Overlay */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="absolute inset-0 bg-gradient-to-b from-gray-900/80 via-gray-900/50 to-gray-900"
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Content */}
        <div className="relative mx-auto max-w-[1400px] px-4 pt-20">
          <div className="flex min-h-[calc(100vh-160px)] flex-col items-center justify-center text-center">
            {/* Main Title */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="mb-6 text-6xl font-bold tracking-tight text-white"
            >
              {language === 'en-US' ? (
                <>
                  Discover Your Next
                  <br />
                  Favorite{' '}
                  <motion.span
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, y: 1 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="text-red-600"
                  >
                    Movie
                  </motion.span>
                </>
              ) : (
                <>
                  Khám Phá
                  <br />
                  <motion.span
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, y: 1 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="text-red-600"
                  >
                    Phim
                  </motion.span>
                  Yêu Thích
                </>
              )}
            </motion.h1>

            {/* Description - Full content with fixed container */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mb-8 flex justify-center"
            >
              <div className="flex min-h-[80px] max-w-2xl items-center">
                <p className="text-lg text-gray-300">
                  {currentMovie?.description?.[language === 'en-US' ? 'en' : 'vi'] ||
                    (language === 'en-US'
                      ? 'Discover your next favorite movie with our personalized recommendations.'
                      : 'Khám phá bộ phim yêu thích tiếp theo của bạn với các đề xuất được cá nhân hóa của chúng tôi.')}
                </p>
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mb-6 flex gap-4"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex h-11 items-center justify-center rounded-md bg-red-600 px-8 text-sm font-medium text-white transition-colors hover:bg-red-700"
              >
                {language === 'en-US' ? 'Explore Movies' : 'Khám Phá Phim'}
                <motion.span
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="ml-3 flex items-center"
                >
                  <svg
                    className="size-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    />
                  </svg>
                </motion.span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex h-11 items-center justify-center rounded-md border border-gray-600 px-8 text-sm font-medium text-white transition-colors hover:bg-white/50"
              >
                {language === 'en-US' ? 'How It Works' : 'Hướng Dẫn'}
              </motion.button>
            </motion.div>

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

            {/* Scroll Indicator - Updated positioning */}
            <div className="mt-16 flex w-full justify-center">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{
                  opacity: 1,
                  y: [0, 10, 0],
                }}
                transition={{
                  opacity: { duration: 0.6, delay: 1 },
                  y: {
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  },
                }}
                className="flex flex-col items-center text-gray-400 transition-colors hover:text-gray-300"
              >
                <button
                  onClick={scrollToHowItWorks}
                  className="flex flex-col items-center text-gray-400 transition-colors hover:text-gray-300"
                >
                  <span className="mb-2 text-sm">
                    {language === 'en-US' ? 'Learn More' : 'Tìm Hiểu Thêm'}
                  </span>
                  <motion.svg
                    className="size-6 animate-bounce"
                    fill="none"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <motion.path
                      d="M19 14l-7 7m0 0l-7-7m7 7V3"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  </motion.svg>
                </button>
                {/* Slide Navigation Dots - Updated with interaction handler */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.8 }}
                  className="mt-4 flex w-full justify-center gap-2"
                >
                  {featuredMovies.map((movie, index) => (
                    <motion.button
                      key={movie.id}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleSlideInteraction(index)}
                      className={`size-2 rounded-full transition-all ${
                        index === currentSlide ? 'w-8 bg-red-600' : 'bg-gray-600 hover:bg-gray-500'
                      } ${isPaused && index === currentSlide ? 'ring-2 ring-white/50' : ''}`}
                      aria-label={`Go to slide ${index + 1}`}
                    />
                  ))}
                </motion.div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Pause indicator - only visible when paused */}
        <AnimatePresence>
          {isPaused && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-24 right-8 flex items-center gap-2 rounded-full bg-black/30 px-3 py-1 text-xs text-white"
            >
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="size-2 rounded-full bg-red-600"
              ></motion.span>
              <span>Paused</span>
            </motion.div>
          )}
        </AnimatePresence>
      </section>
      {/* How it works sections */}
      <section ref={howItWorksRef} className="relative bg-gray-900 py-20">
        <div className="absolute  bg-gradient-to-b from-transparent via-gray-900 to-gray-900" />
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9 }}
            className="text-center"
          >
            <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
              How MovieMate Works?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
              Get Personalized Movie Recommendations in just a few simple steps
            </p>
          </motion.div>
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {/* Step 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              whileHover={{ scale: 1.05, transition: { duration: 0.2 } }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="absolute -top-4 left-1/2 flex size-8 -translate-x-1/2 items-center justify-center rounded-full bg-red-600 text-sm font-bold text-white transition-transform duration-300 group-hover:scale-110">
                <motion.span
                  initial={{ opacity: 0, scale: 0.5 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    type: 'spring',
                    stiffness: 260,
                    damping: 20,
                  }}
                  className="inline-block"
                >
                  1
                </motion.span>
              </div>
              <div className="mb-4 flex items-center justify-center">
                <div className="rounded-full bg-red-600/10 p-3 transition-colors duration-300 group-hover:bg-red-600/20">
                  <svg
                    className="size-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              </div>
              <h3 className="mb-2 text-center text-lg font-semibold text-white">
                Create an Account
              </h3>
              <p className="text-center text-sm text-gray-400">
                Sign up for free and set up your profile with your movie preferences.
              </p>
            </motion.div>

            {/* Step 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              whileHover={{ scale: 1.05, transition: { duration: 0.2 } }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="absolute -top-4 left-1/2 flex size-8 -translate-x-1/2 items-center justify-center rounded-full bg-red-600 text-sm font-bold text-white transition-transform duration-300 group-hover:scale-110">
                <motion.span
                  initial={{ opacity: 0, scale: 0.5 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    type: 'spring',
                    stiffness: 260,
                    damping: 20,
                  }}
                  className="inline-block"
                >
                  2
                </motion.span>
              </div>
              <div className="mb-4 flex items-center justify-center">
                <div className="rounded-full bg-red-600/10 p-3 transition-colors duration-300 group-hover:bg-red-600/20">
                  <svg
                    className="size-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                    />
                  </svg>
                </div>
              </div>
              <h3 className="mb-2 text-center text-lg font-semibold text-white">Rate Movies</h3>
              <p className="text-center text-sm text-gray-400">
                Rate movies you've watched to help our algorithm understand your taste.
              </p>
            </motion.div>

            {/* Step 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              whileHover={{ scale: 1.05, transition: { duration: 0.2 } }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="absolute -top-4 left-1/2 flex size-8 -translate-x-1/2 items-center justify-center rounded-full bg-red-600 text-sm font-bold text-white transition-transform duration-300 group-hover:scale-110">
                <motion.span
                  initial={{ opacity: 0, scale: 0.5 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    type: 'spring',
                    stiffness: 260,
                    damping: 20,
                  }}
                  className="inline-block"
                >
                  3
                </motion.span>
              </div>
              <div className="mb-4 flex items-center justify-center">
                <div className="rounded-full bg-red-600/10 p-3 transition-colors duration-300 group-hover:bg-red-600/20">
                  <svg
                    className="size-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
              </div>
              <h3 className="mb-2 text-center text-lg font-semibold text-white">
                Get Recommendations
              </h3>
              <p className="text-center text-sm text-gray-400">
                Receive personalized movie suggestions based on your ratings and preferences.
              </p>
            </motion.div>

            {/* Step 4 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              whileHover={{ scale: 1.05, transition: { duration: 0.2 } }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="absolute -top-4 left-1/2 flex size-8 -translate-x-1/2 items-center justify-center rounded-full bg-red-600 text-sm font-bold text-white transition-transform duration-300 group-hover:scale-110">
                <motion.span
                  initial={{ opacity: 0, scale: 0.5 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    type: 'spring',
                    stiffness: 260,
                    damping: 20,
                  }}
                  className="inline-block"
                >
                  4
                </motion.span>
              </div>
              <div className="mb-4 flex items-center justify-center">
                <div className="rounded-full bg-red-600/10 p-3 transition-colors duration-300 group-hover:bg-red-600/20">
                  <svg
                    className="size-6 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                    />
                  </svg>
                </div>
              </div>
              <h3 className="mb-2 text-center text-lg font-semibold text-white">
                Build Your Watchlist
              </h3>
              <p className="text-center text-sm text-gray-400">
                Save movies to your watchlist and track what you want to watch next.
              </p>
            </motion.div>
          </div>
        </div>
      </section>
      {/* Why choose MovieMate */}
      <section>
        <div className="relative bg-black py-20">
          <div className="inset-0 bg-gradient-to-b">
            <div className="container mx-auto px-4">
              <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
                Why choose MovieMate
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
                We're more than just a movie database. We're your personal cinema companion.
              </p>
              {/* Grid of Card */}
              <div className="mt-16 grid grid-cols-1 gap-12 md:grid-cols-3">
                {/* Card 1 */}
                <div className="group relative rounded-lg bg-gray-800/50 p-8 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500">
                  <div className="mb-8 flex items-center justify-center">
                    <div className="rounded-full bg-red-600/10 p-4 transition-colors duration-300 group-hover:bg-red-600/20">
                      {/* icon Movie */}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="size-8 text-red-600"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-3.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-1.5A1.125 1.125 0 0 1 18 18.375M20.625 4.5H3.375m17.25 0c.621 0 1.125.504 1.125 1.125M20.625 4.5h-1.5C18.504 4.5 18 5.004 18 5.625m3.75 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 4.5c-.621 0-1.125.504-1.125 1.125M3.375 4.5h1.5C5.496 4.5 6 5.004 6 5.625m-3.75 0v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75C5.496 8.25 6 7.746 6 7.125v-1.5M4.875 8.25C5.496 8.25 6 8.754 6 9.375v1.5m0-5.25v5.25m0-5.25C6 5.004 6.504 4.5 7.125 4.5h9.75c.621 0 1.125.504 1.125 1.125m1.125 2.625h1.5m-1.5 0A1.125 1.125 0 0 1 18 7.125v-1.5m1.125 2.625c-.621 0-1.125.504-1.125 1.125v1.5m2.625-2.625c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M18 5.625v5.25M7.125 12h9.75m-9.75 0A1.125 1.125 0 0 1 6 10.875M7.125 12C6.504 12 6 12.504 6 13.125m0-2.25C6 11.496 5.496 12 4.875 12M18 10.875c0 .621-.504 1.125-1.125 1.125M18 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m-12 5.25v-5.25m0 5.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125m-12 0v-1.5c0-.621-.504-1.125-1.125-1.125M18 18.375v-5.25m0 5.25v-1.5c0-.621.504-1.125 1.125-1.125M18 13.125v1.5c0 .621.504 1.125 1.125 1.125M18 13.125c0-.621.504-1.125 1.125-1.125M6 13.125v1.5c0 .621-.504 1.125-1.125 1.125M6 13.125C6 12.504 5.496 12 4.875 12m-1.5 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M19.125 12h1.5m0 0c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h1.5m14.25 0h1.5"
                        />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-4 text-center text-xl font-semibold text-white">
                    Personalized Recommendations
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    Our advanced algorithm learns your preferences and suggests movies you'll love.
                  </p>
                </div>

                {/* Card 2 */}
                <div className="group relative rounded-lg bg-gray-800/50 p-8 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500">
                  <div className="mb-8 flex items-center justify-center">
                    <div className="rounded-full bg-red-600/10 p-4 transition-colors duration-300 group-hover:bg-red-600/20">
                      <svg
                        className="size-8 text-red-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                        />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-4 text-center text-xl font-semibold text-white">
                    Curated Collections
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    Explore hand-picked collections for every mood, genre, and occasion.
                  </p>
                </div>

                {/* Card 3 */}
                <div className="group relative rounded-lg bg-gray-800/50 p-8 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500">
                  <div className="mb-8 flex items-center justify-center">
                    <div className="rounded-full bg-red-600/10 p-4 transition-colors duration-300 group-hover:bg-red-600/20">
                      <svg
                        className="size-8 text-red-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87M16 7a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-4 text-center text-xl font-semibold text-white">
                    Social Watching
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    Share your favorites, create watch parties, and see what your friends are
                    enjoying.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      {/* Latest Releases */}
      <section className="relative bg-gradient-to-b from-gray-900 via-gray-900 to-black py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">Latest Releases</h2>
          <p className="pt-5 text-center text-lg text-gray-400">
            Check out the newest additions to our extensive movie collection
          </p>
          <div className="mt-10">
            <TabGroup tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />
            <MovieGrid movies={moviesByTab[activeTab]} loading={tabLoading} error={tabError} />
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mt-8 flex justify-center"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                //  onClick={() =>{
                //  }}
                className="flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-red-700"
              >
                View All Movies
                <motion.span
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="ml-2 flex items-center"
                >
                  <svg
                    className="size-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    />
                  </svg>
                </motion.span>
              </motion.button>
            </motion.div>
          </div>
        </div>
      </section>
      {/* Explore Categories */}
      <section className="relative bg-gray-900 bg-gradient-to-b from-transparent via-gray-900 to-gray-900 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            Explore Categories
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
            From heart-pounding action to thought-provoking dramas, we have something for everyone.
          </p>
          {catLoading && <div className="text-center text-white">Loading...</div>}
          {catError && <div className="text-center text-red-500">{catError.message}</div>}
          {categories && <CategoryGrid categories={categories} />}
          <div className="mt-8 flex justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              //  onClick={() =>{
              //  }}
              className="flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-red-700"
            >
              View All Categories
            </motion.button>
          </div>
        </div>
      </section>
      {/* Choose Your Plan */}
      <sections className="relative bg-gradient-to-b from-black via-gray-900 to-gray-900 py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
              Choose Your Plan
            </h2>
            <p className="pt-5 text-center text-lg text-gray-400">
              Select the perfect plan that fits your viewing habits.
            </p>
          </motion.div>

          {/* Pricing Cards Container */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16 flex flex-col items-center justify-center gap-8 py-10 md:flex-row"
          >
            <PlanList />
          </motion.div>

          {/* Additional Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 text-center"
          >
            <p className="text-gray-400">
              All plans include a 14-day free trial. No credit card required.
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="mt-4  text-lg text-red-500 hover:text-red-400"
            >
              Compare all features →
            </motion.button>
          </motion.div>
        </div>
      </sections>
      <section className="relative bg-gradient-to-b from-black via-black to-gray-900 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            What Our Users Say
          </h2>
          <p className="pt-5 text-center text-lg text-gray-400">
            Join thousands of movie enthusiasts who have found their perfect watch with MovieMate.
          </p>

          {/* Testimonials Grid */}
          <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Testimonial 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="mb-4 flex items-center gap-4">
                <img
                  src="https://randomuser.me/api/portraits/women/1.jpg"
                  alt="Sarah Johnson"
                  className="size-12 rounded-full object-cover ring-2 ring-red-500"
                />
                <div>
                  <h3 className="font-semibold text-white">Sarah Johnson</h3>
                  <div className="flex text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="size-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-gray-300">
                "MovieMate has completely transformed how I discover films. The recommendations are
                spot-on, and I've found so many hidden gems I would have never known about!"
              </p>
            </motion.div>

            {/* Testimonial 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="mb-4 flex items-center gap-4">
                <img
                  src="https://randomuser.me/api/portraits/men/2.jpg"
                  alt="Michael Chen"
                  className="size-12 rounded-full object-cover ring-2 ring-red-500"
                />
                <div>
                  <h3 className="font-semibold text-white">Michael Chen</h3>
                  <div className="flex text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="size-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-gray-300">
                "The social features are amazing! I love being able to see what my friends are
                watching and share my favorite movies with them. It's like having a movie club in
                your pocket."
              </p>
            </motion.div>

            {/* Testimonial 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="group relative rounded-lg bg-gray-800/50 p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-gray-800/70 hover:ring-2 hover:ring-red-500"
            >
              <div className="mb-4 flex items-center gap-4">
                <img
                  src="https://randomuser.me/api/portraits/women/3.jpg"
                  alt="Emma Rodriguez"
                  className="size-12 rounded-full object-cover ring-2 ring-red-500"
                />
                <div>
                  <h3 className="font-semibold text-white">Emma Rodriguez</h3>
                  <div className="flex text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="size-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-gray-300">
                "I've discovered so many international films through MovieMate. The curated
                collections are fantastic, and the app makes it easy to explore different genres and
                cultures."
              </p>
            </motion.div>
          </div>

          {/* View More Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 flex justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-red-700"
            >
              Read More Reviews
              <motion.span
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="ml-2 flex items-center"
              >
                <svg
                  className="size-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </motion.span>
            </motion.button>
          </motion.div>
        </div>
      </section>

      <section className="flex w-full justify-center bg-black py-16">
        <div className="w-full max-w-7xl rounded-2xl bg-gradient-to-r from-red-900 via-gray-900 to-gray-800 py-10">
          <h2 className="pt-10 text-center text-4xl font-bold text-white">
            Ready to Start Your Movie Journey?
          </h2>
          <p className="pt-5 text-center text-lg text-gray-300">
            Join MovieMate today and discover a new world of cinema tailored just for you. No
            subscription required.
          </p>
          {/* Get Started Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 flex justify-center "
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="durations-300  flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-red-700"
            >
              Get Started Now
              <motion.span
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="ml-2 flex items-center "
              >
                <svg
                  className="size-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </motion.span>
            </motion.button>
          </motion.div>
          <div className="mx-auto mt-8 grid max-w-fit grid-cols-1 justify-items-center gap-x-8 gap-y-4 sm:grid-cols-2 md:grid-cols-2">
            {features.map((feature, idx) => (
              <div key={idx} className="flex items-center text-sm text-green-400">
                <CheckCircle className="mr-2 size-5" />
                <span className="text-white">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
