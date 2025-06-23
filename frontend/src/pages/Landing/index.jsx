import { AccountCircle, Logout, Settings } from '@mui/icons-material';
import { IconButton, Menu, MenuItem, Tooltip } from '@mui/material';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle } from 'lucide-react';
import { useEffect, useRef, useState, useMemo, useCallback, lazy } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

// Lazy load các component nặng để tối ưu performance
const CategoriesSection = lazy(() => import('../../components/categories/CategoriesSection'));
const LandingFooter = lazy(() => import('../../components/footer/LandingFooter'));
const MovieGrid = lazy(() => import('../../components/movies/movie-grid/MovieGrid'));
const TabGroup = lazy(() => import('../../components/movies/tab-group'));
const PlanList = lazy(() => import('../../components/plans/PlanList'));
const MovieTrailerModal = lazy(
  () => import('../../components/movies/movie-trailer/MovieTrailerModal')
);

// Import các component nhẹ trực tiếp
import MovieMateLogo from '../../components/header/Logo';
import LanguageSwitcher from '../../components/language/LanguageSwitcher';
import { LazyLoader, GridSkeleton } from '../../components/common/LazyLoader';
import {
  useFeaturedMovies,
  useTrendingMovies,
  useTopRatedMovies,
  useUpcomingMovies,
} from '../../hooks/useMovies';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { logout } from '../../store/slices/authSlice';
import { setCurrentTab } from '../../store/slices/movieSlice';
import { useTrailerModal } from '../../hooks/useTrailerModal';

const TABS = [
  { key: 'trending', label: 'latestReleases.tabs.trending' },
  { key: 'topRated', label: 'latestReleases.tabs.topRated' },
  { key: 'upcoming', label: 'latestReleases.tabs.upcoming' },
];

const LandingPage = () => {
  const { t, i18n, app_language } = useTranslation('landing');
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [anchorEl, setAnchorEl] = useState(null);
  const user = useSelector(state => state.auth.user);
  const currentTab = useSelector(state => state.movies.currentTab);
  const [isSecondaryDataEnabled, setIsSecondaryDataEnabled] = useState(false);

  // Use the trailer modal hook
  const {
    isTrailerOpen,
    modalMovie,
    modalTrailerUrl,
    handleTrailerClick,
    closeTrailerModal,
    getTrailerUrl,
  } = useTrailerModal();

  // Custom hooks cho fetch phim
  const {
    data: featuredMovies = [],
    isLoading: featuredLoading,
    error: featuredError,
  } = useFeaturedMovies();

  const secondaryOptions = { enabled: isSecondaryDataEnabled };

  const { data: trendingMovies = [], isLoading: trendingLoading } =
    useTrendingMovies(secondaryOptions);
  const { data: topRatedMovies = [], isLoading: topRatedLoading } =
    useTopRatedMovies(secondaryOptions);
  const { data: upcomingMovies = [], isLoading: upcomingLoading } =
    useUpcomingMovies(secondaryOptions);

  // Effect to enable secondary data fetching after a delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsSecondaryDataEnabled(true);
    }, 2000); // Delay of 2 seconds

    return () => clearTimeout(timer);
  }, []);

  // Memoize features
  const features = useMemo(
    () => [
      t('features.items.library'),
      t('features.items.recommendations'),
      t('features.items.watchlist'),
      t('features.items.reviews'),
    ],
    [t]
  );

  // Memoize translated tabs
  const translatedTabs = useMemo(
    () =>
      TABS.map(tab => ({
        ...tab,
        label: t(tab.label),
      })),
    [t]
  );

  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const pauseTimeoutRef = useRef(null);
  const howItWorksRef = useRef(null);

  const SLIDE_INTERVAL = 3000; // 5 seconds between slides
  const PAUSE_DURATION = 5000; // 15 seconds pause after user interaction

  // Lấy ngôn ngữ hiện tại
  // const currentLang = i18n.language === 'vi' ? 'vi-VN' : 'en-US';

  // Memo hóa dữ liệu phim theo tab
  const movies = useMemo(() => {
    switch (currentTab) {
      case 'trending':
        return trendingMovies;
      case 'topRated':
        return topRatedMovies;
      case 'upcoming':
        return upcomingMovies;
      default:
        return [];
    }
  }, [currentTab, trendingMovies, topRatedMovies, upcomingMovies]);

  // Memo hóa loading theo tab
  const loading = useMemo(() => {
    switch (currentTab) {
      case 'trending':
        return trendingLoading;
      case 'topRated':
        return topRatedLoading;
      case 'upcoming':
        return upcomingLoading;
      default:
        return false;
    }
  }, [currentTab, trendingLoading, topRatedLoading, upcomingLoading]);

  // Slide show interval with pause functionality
  useEffect(() => {
    if (!isPaused && featuredMovies.length > 0) {
      const intervalId = setInterval(() => {
        setCurrentSlide(prev => (prev + 1) % featuredMovies.length);
      }, SLIDE_INTERVAL);

      return () => clearInterval(intervalId);
    }
  }, [isPaused, featuredMovies.length]);

  // Memoize handler for slide interaction
  const handleSlideInteraction = useCallback(index => {
    if (pauseTimeoutRef.current) {
      clearTimeout(pauseTimeoutRef.current);
    }
    setCurrentSlide(index);
    setIsPaused(true);
    pauseTimeoutRef.current = setTimeout(() => {
      setIsPaused(false);
    }, PAUSE_DURATION);
  }, []);

  const scrollToHowItWorks = useCallback(() => {
    howItWorksRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleProfileMenuOpen = useCallback(event => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleProfileMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  const handleProfileClick = useCallback(() => {
    handleProfileMenuClose();
    navigate(`/profile/${user.id}`);
  }, [handleProfileMenuClose, navigate, user?.id]);

  const handleSettingsClick = useCallback(() => {
    handleProfileMenuClose();
    navigate('/settings');
  }, [handleProfileMenuClose, navigate]);

  const handleLogout = useCallback(() => {
    handleProfileMenuClose();
    dispatch(logout());
    navigate('/login');
  }, [handleProfileMenuClose, dispatch, navigate]);

  // Memoize tab change handler
  const handleTabChange = useCallback(tab => dispatch(setCurrentTab(tab)), [dispatch]);

  // Xử lý error/loading cho featuredMovies
  if (featuredError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-red-600">
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{featuredError.message}</p>
        </div>
      </div>
    );
  }

  if (featuredLoading || !Array.isArray(featuredMovies) || featuredMovies.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="size-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent"></div>
      </div>
    );
  }

  const currentMovie = featuredMovies[currentSlide];
  const trailerUrl = getTrailerUrl(currentMovie);

  return (
    <div className="relative min-h-screen bg-gray-900">
      {/* Navigation Header */}
      <header className="absolute inset-x-0 top-0 z-10">
        <div className="mx-auto max-w-[1400px] px-4">
          <div className="flex h-20 items-center justify-between">
            <MovieMateLogo />
            <div className="flex items-center gap-4">
              <LanguageSwitcher />
              {user && user.id ? (
                <>
                  <Tooltip title={user.username}>
                    <IconButton
                      onClick={handleProfileMenuOpen}
                      size="large"
                      edge="end"
                      aria-label="account of current user"
                      aria-haspopup="true"
                      color="inherit"
                      sx={{ p: 0 }}
                    >
                      <div className="relative">
                        {/* Avatar Container */}
                        <div className="relative size-8 rounded-full bg-gradient-to-br from-red-500 to-red-700 p-0.5 shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl">
                          {/* Always render img if avatar_url exists, but handle error gracefully */}
                          {(user.avatar_url || user.avatarUrl) && (
                            <img
                              src={user.avatar_url || user.avatarUrl}
                              alt={user.username}
                              className="size-full rounded-full border border-gray-800 object-cover"
                              crossOrigin="anonymous"
                              referrerPolicy="no-referrer"
                              onError={e => {
                                e.target.style.display = 'none';
                                e.target.nextElementSibling.style.display = 'flex';
                              }}
                              onLoad={e => {
                                e.target.nextElementSibling.style.display = 'none';
                              }}
                            />
                          )}

                          {/* Fallback Avatar - shown when no avatar_url or when img fails to load */}
                          <div
                            className={`absolute inset-0 size-full items-center justify-center rounded-full border border-gray-800 bg-gradient-to-br from-gray-700 to-gray-800 ${
                              user.avatar_url || user.avatarUrl ? 'hidden' : 'flex'
                            }`}
                          >
                            <span className="text-xs font-bold text-white">
                              {user.username?.[0]?.toUpperCase() || '?'}
                            </span>
                          </div>

                          {/* Online Status Indicator */}
                          <div className="absolute -bottom-0.5 -right-0.5 size-2.5 rounded-full border border-gray-900 bg-green-500 shadow-sm"></div>
                        </div>
                      </div>
                    </IconButton>
                  </Tooltip>
                  <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleProfileMenuClose}
                    PaperProps={{
                      elevation: 0,
                      sx: {
                        overflow: 'visible',
                        filter: 'drop-shadow(0px 8px 32px rgba(0,0,0,0.4))',
                        mt: 1.5,
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '12px',
                        '& .MuiMenuItem-root': {
                          color: '#f3f4f6',
                          padding: '12px 16px',
                          fontSize: '14px',
                          fontWeight: 500,
                          borderRadius: '8px',
                          margin: '4px 8px',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            backgroundColor: '#374151',
                            transform: 'translateX(2px)',
                          },
                          '&:first-of-type': {
                            marginTop: '8px',
                          },
                          '&:last-of-type': {
                            marginBottom: '8px',
                            color: '#ef4444',
                            '&:hover': {
                              backgroundColor: '#fca5a5',
                              color: '#dc2626',
                            },
                          },
                        },
                      },
                    }}
                    transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                    anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  >
                    <MenuItem onClick={handleProfileClick}>
                      <AccountCircle fontSize="small" sx={{ mr: 1.5, color: '#10b981' }} />
                      {t('header.profile')}
                    </MenuItem>
                    <MenuItem onClick={handleSettingsClick}>
                      <Settings fontSize="small" sx={{ mr: 1.5, color: '#6b7280' }} />
                      {t('header.settings')}
                    </MenuItem>
                    <MenuItem onClick={handleLogout}>
                      <Logout fontSize="small" sx={{ mr: 1.5 }} />
                      {t('header.logout')}
                    </MenuItem>
                  </Menu>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate('/login')}
                    className="rounded-md border border-red-600 px-4 py-2 text-red-600 transition-colors hover:bg-red-600 hover:text-white"
                  >
                    {t('header.signIn')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section with Slider */}
      <section className="relative min-h-screen overflow-hidden">
        {/* Background Slides */}
        <AnimatePresence mode="wait">
          {featuredMovies.length > 0 && (
            <motion.div
              key={featuredMovies[currentSlide].id}
              initial={{ opacity: 0, scale: 1.1 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              transition={{ duration: 0.8, ease: 'easeInOut' }}
              className="absolute inset-0"
            >
              {/* Background Image: Use an <img> tag for prioritization */}
              {/* eslint-disable-next-line react/no-unknown-property */}
              <img
                key={featuredMovies[currentSlide].id}
                src={featuredMovies[currentSlide].poster_path || '/placeholder-poster.jpg'}
                alt={`Poster for ${featuredMovies[currentSlide].title}`}
                fetchPriority="high"
                className="absolute inset-0 size-full object-cover"
              />

              {/* Gradient Overlay */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="absolute inset-0 bg-gradient-to-b from-gray-900/80 via-gray-900/50 to-gray-900"
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="relative mx-auto max-w-[1400px] px-4 pt-20">
          <div className="flex min-h-[calc(100vh-160px)] flex-col items-center justify-center text-center">
            {/* Main Title */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="mb-4 text-3xl font-bold tracking-tight text-white sm:mb-6 sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl"
            >
              {app_language === 'en' ? (
                <>
                  <span className="block leading-tight sm:leading-tight md:leading-tight lg:leading-tight xl:leading-tight">
                    Discover Your Next
                  </span>
                  <span className="block leading-tight sm:leading-tight md:leading-tight lg:leading-tight xl:leading-tight">
                    Favorite{' '}
                    <motion.span
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, y: 1 }}
                      transition={{ duration: 0.5, delay: 0.4 }}
                      className="text-red-600"
                    >
                      Movie
                    </motion.span>
                  </span>
                </>
              ) : (
                <>
                  <span className="block leading-tight sm:leading-tight md:leading-tight lg:leading-tight xl:leading-tight">
                    Khám Phá
                  </span>
                  <span className="block leading-tight sm:leading-tight md:leading-tight lg:leading-tight xl:leading-tight">
                    <motion.span
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, y: 1 }}
                      transition={{ duration: 0.5, delay: 0.4 }}
                      className="text-red-600"
                    >
                      Phim
                    </motion.span>
                    Yêu Thích
                  </span>
                </>
              )}
            </motion.h1>

            {/* Description */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mb-8 flex justify-center"
            >
              <div className="flex min-h-[80px] max-w-2xl items-center">
                <p className="text-lg text-gray-300">
                  {currentMovie?.[i18n.language === 'en' ? 'overview_en' : 'overview_vi'] ||
                    'Khám phá bộ phim yêu thích tiếp theo của bạn với các đề xuất được cá nhân hóa của chúng tôi.'}
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
                {t('hero.exploreMovies')}
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
                {t('hero.howItWorks')}
              </motion.button>
            </motion.div>

            {/* Featured Movie Info */}
            <div className="text-center">
              <p className="mb-4 text-sm uppercase tracking-wider text-gray-400">
                {t('hero.nowFeaturing')}
              </p>
              <h2 className="mb-2 text-2xl font-bold text-white">
                {currentMovie?.title}
                {currentMovie?.original_title &&
                  currentMovie.original_title !== currentMovie.title && (
                    <span className="ml-2 text-lg font-normal text-gray-400">
                      ({currentMovie.original_title})
                    </span>
                  )}
              </h2>
              <div className="mb-4 flex items-center justify-center gap-2">
                <div className="flex">
                  {[1, 2, 3, 4, 5].map(star => (
                    <span
                      key={star}
                      className={`text-lg ${
                        star <= Math.round((currentMovie?.vote_average || 0) / 2)
                          ? 'text-yellow-400'
                          : 'text-gray-400'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                <span className="ml-1 font-medium text-white">
                  {currentMovie?.vote_average
                    ? `${Math.round(currentMovie.vote_average / 2)}/5`
                    : 'N/A'}
                </span>
                <span className="text-gray-400">
                  | {new Date(currentMovie?.release_date).getFullYear()}
                </span>
              </div>
              <button
                onClick={() => handleTrailerClick(currentMovie)}
                className={`inline-flex items-center justify-center rounded-md border border-red-600 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-600 hover:text-white ${
                  !trailerUrl ? 'cursor-not-allowed opacity-50' : ''
                }`}
                disabled={!trailerUrl}
              >
                <span className="mr-2">▶</span>
                {t('hero.watchTrailer')}
              </button>
            </div>

            {/* Scroll Indicator */}
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
                  <span className="mb-2 text-sm">{t('hero.learnMore')}</span>
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
                {/* Slide Navigation Dots */}
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
              {t('howItWorks.title')}
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
              {t('howItWorks.subtitle')}
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
                {t('howItWorks.step1.title')}
              </h3>
              <p className="text-center text-sm text-gray-400">
                {t('howItWorks.step1.description')}
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
              <h3 className="mb-2 text-center text-lg font-semibold text-white">
                {t('howItWorks.step2.title')}
              </h3>
              <p className="text-center text-sm text-gray-400">
                {t('howItWorks.step2.description')}
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
                {t('howItWorks.step3.title')}
              </h3>
              <p className="text-center text-sm text-gray-400">
                {t('howItWorks.step3.description')}
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
                {t('howItWorks.step4.title')}
              </h3>
              <p className="text-center text-sm text-gray-400">
                {t('howItWorks.step4.description')}
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
                {t('whyChoose.title')}
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
                {t('whyChoose.subtitle')}
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
                    {t('whyChoose.card1.title')}
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    {t('whyChoose.card1.description')}
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
                    {t('whyChoose.card2.title')}
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    {t('whyChoose.card2.description')}
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
                    {t('whyChoose.card3.title')}
                  </h3>
                  <p className="text-center text-base text-gray-300">
                    {t('whyChoose.card3.description')}
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
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            {t('latestReleases.title')}
          </h2>
          <p className="pt-5 text-center text-lg text-gray-400">{t('latestReleases.subtitle')}</p>
          <div className="mt-10">
            <LazyLoader
              fallback={<div className="h-12 bg-gray-800 rounded animate-pulse mb-4"></div>}
            >
              <TabGroup
                tabs={translatedTabs}
                activeTab={currentTab}
                onTabChange={handleTabChange}
              />
            </LazyLoader>
            <LazyLoader fallback={<GridSkeleton count={6} />}>
              <MovieGrid
                movies={movies}
                loading={loading}
                error={featuredError}
                onTrailerClick={handleTrailerClick}
              />
            </LazyLoader>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mt-8 flex justify-center"
            >
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-red-700"
              >
                {t('latestReleases.viewAllMovies')}
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
      <LazyLoader fallback={<div className="h-96 bg-gray-800 rounded animate-pulse"></div>}>
        <CategoriesSection />
      </LazyLoader>
      {/* Choose Your Plan */}
      <section className="relative bg-gradient-to-b from-black via-gray-900 to-gray-900 py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
              {t('chooseYourPlan.title')}
            </h2>
            <p className="pt-5 text-center text-lg text-gray-400">{t('chooseYourPlan.subtitle')}</p>
          </motion.div>

          {/* Pricing Cards Container */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16 flex flex-col items-center justify-center gap-8 py-10 md:flex-row"
          >
            <LazyLoader fallback={<div className="h-64 bg-gray-800 rounded animate-pulse"></div>}>
              <PlanList onSelectPlan={plan => navigate(`/checkout?plan=${plan.id}`)} />
            </LazyLoader>
          </motion.div>

          {/* Additional Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-8 text-center"
          >
            <p className="text-gray-400">{t('chooseYourPlan.additionalInfo')}</p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="mt-4  text-lg text-red-500 hover:text-red-400"
              onClick={() => navigate('/pricing')}
            >
              {t('chooseYourPlan.compareFeatures')}
            </motion.button>
          </motion.div>
        </div>
      </section>
      <section className="relative bg-gradient-to-b from-black via-black to-gray-900 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            {t('testimonials.title')}
          </h2>
          <p className="pt-5 text-center text-lg text-gray-400">{t('testimonials.subtitle')}</p>

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
              <p className="text-gray-300">{t('testimonials.testimonial1.text')}</p>
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
              <p className="text-gray-300">{t('testimonials.testimonial2.text')}</p>
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
              <p className="text-gray-300">{t('testimonials.testimonial3.text')}</p>
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
              {t('testimonials.viewMore')}
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
            {t('getStarted.title')}
          </h2>
          <p className="pt-5 text-center text-lg text-gray-300">{t('getStarted.subtitle')}</p>
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
              {t('getStarted.cta')}
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
      <LazyLoader fallback={<div className="h-96 bg-gray-800 rounded animate-pulse"></div>}>
        <MovieTrailerModal
          isOpen={isTrailerOpen}
          onClose={closeTrailerModal}
          movie={modalMovie}
          trailerUrl={modalTrailerUrl}
        />
      </LazyLoader>
      <LazyLoader fallback={<div className="h-64 bg-gray-800 rounded animate-pulse"></div>}>
        <LandingFooter />
      </LazyLoader>
    </div>
  );
};

export default LandingPage;
