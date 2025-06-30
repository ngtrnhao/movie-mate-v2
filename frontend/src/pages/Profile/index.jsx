import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchProfile,
  fetchUserStats,
  fetchUserReviews,
  fetchUserRatings,
  fetchFavoriteGenres,
} from '../../store/slices/profileSlice';
import {
  selectProfile,
  selectProfileLoading,
  selectProfileError,
  selectUserStats,
  selectUserReviews,
  selectUserRatings,
  selectFavoriteGenres,
} from '../../store/selectors/profileSelectors';
import { CircularProgress, Alert, Tabs, Tab, IconButton } from '@mui/material';
import { LocationOn, CalendarToday, Email, Share, MoreVert } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
// import ReviewList from './components/ReviewList';
import RatingList from './components/RatingList';
import StatsCard from './components/StatsCard';
import GenreList from './components/GenreList';
import UserBadge from '../../components/common/UserBadge';
import { format } from 'date-fns';

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`profile-tabpanel-${index}`}
    aria-labelledby={`profile-tab-${index}`}
    {...other}
    className="mt-6"
  >
    {value === index && children}
  </div>
);

const StyledTabs = styled(Tabs)({
  '& .MuiTab-root': {
    color: '#fff',
    fontSize: '0.95rem',
    fontWeight: 500,
    textTransform: 'none',
    transition: 'all 0.2s',
    '&:hover': {
      color: '#ef4444',
      backgroundColor: 'rgba(239, 68, 68, 0.05)',
    },
    '&.Mui-selected': {
      color: '#ef4444',
      fontWeight: 600,
    },
  },
});

const Profile = () => {
  const { userId } = useParams();
  const dispatch = useDispatch();
  const [tabValue, setTabValue] = React.useState(0);

  const profile = useSelector(selectProfile);
  const loading = useSelector(selectProfileLoading);
  const error = useSelector(selectProfileError);
  const stats = useSelector(selectUserStats);
  const reviews = useSelector(selectUserReviews);
  const ratings = useSelector(selectUserRatings);
  const favoriteGenres = useSelector(selectFavoriteGenres);

  useEffect(() => {
    if (userId) {
      dispatch(fetchProfile(userId));
      dispatch(fetchUserStats(userId));
      dispatch(fetchUserReviews({ userId }));
      dispatch(fetchUserRatings({ userId }));
      dispatch(fetchFavoriteGenres({ userId }));
    }
  }, [dispatch, userId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <div className="flex min-h-screen items-center justify-center">
          <CircularProgress size={60} thickness={4} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="mx-auto max-w-4xl">
          <Alert severity="error" className="rounded-lg shadow-lg">
            {error}
          </Alert>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="mx-auto max-w-4xl">
          <Alert severity="info" className="rounded-lg shadow-lg">
            Profile not found
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 pb-12 pt-32">
      <div className="mx-auto max-w-6xl px-4">
        {/* Cover Section */}
        <div className="relative mb-6 h-64 overflow-hidden rounded-3xl bg-gradient-to-br from-gray-800 to-gray-900"></div>

        {/* Profile Header */}
        <div className="relative z-10 -mt-20 rounded-3xl border border-gray-700 bg-gray-800/95 p-8 shadow-2xl backdrop-blur-sm">
          <div className="grid grid-cols-1 items-center gap-8 md:grid-cols-3">
            <div className="flex flex-col items-center">
              <div className="relative mb-4">
                {/* Avatar Container */}
                <div className="relative size-32 rounded-full bg-gradient-to-br from-red-500 to-red-700 p-1 shadow-2xl">
                  {/* Always render img if avatar_url exists, but handle error gracefully */}
                  {(profile.avatar_url || profile.avatarUrl) && (
                    <img
                      src={profile.avatar_url || profile.avatarUrl}
                      alt={profile.username}
                      className="size-full rounded-full border-4 border-gray-800 object-cover shadow-xl"
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
                    className={`absolute inset-0 size-full items-center justify-center rounded-full border-4 border-gray-800 bg-gradient-to-br from-gray-700 to-gray-800 shadow-xl ${
                      profile.avatar_url || profile.avatarUrl ? 'hidden' : 'flex'
                    }`}
                  >
                    <span className="text-5xl font-bold text-white">
                      {profile.username?.[0]?.toUpperCase() || '?'}
                    </span>
                  </div>

                  {/* Online Status Indicator */}
                  <div className="absolute bottom-2 right-2 size-6 rounded-full border-4 border-gray-800 bg-green-500 shadow-lg"></div>

                  {/* Upload Avatar Button (hover overlay) */}
                  <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/0 opacity-0 transition-all duration-300 hover:bg-black/50 hover:opacity-100">
                    <button className="rounded-full bg-white/20 p-2 text-white backdrop-blur-sm transition-all hover:bg-white/30">
                      <svg className="size-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Verification Badge */}
                {profile.is_verified && (
                  <div className="absolute -right-1 -top-1 flex size-8 items-center justify-center rounded-full bg-blue-500 text-white shadow-lg">
                    <svg className="size-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>

              {/* User Badge */}
              <UserBadge user={profile} size="md" />
            </div>

            <div className="md:col-span-1">
              <h1 className="mb-4 text-4xl font-bold text-white">{profile.username}</h1>

              <p className="mb-4 leading-relaxed text-gray-300">
                {profile.bio || 'Movie enthusiast exploring the world of cinema 🎬'}
              </p>

              <div className="mb-4 flex flex-wrap gap-4 text-sm text-gray-400">
                {profile.location && (
                  <div className="flex items-center gap-1">
                    <LocationOn fontSize="small" />
                    <span>{profile.location}</span>
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <CalendarToday fontSize="small" />
                  <span>
                    Joined{' '}
                    {profile.date_joined
                      ? format(new Date(profile.date_joined), 'MMM yyyy')
                      : 'Recently'}
                  </span>
                </div>
              </div>

              {/* Subscription Info */}
              {profile.user_type && profile.subscription_end_date && (
                <div className="rounded-2xl border border-red-600 bg-gray-800/95 p-4">
                  <p className="font-bold text-red-600">
                    Current Plan: {profile.user_type.replace('premium_', '').toUpperCase()}
                  </p>
                  <p className="text-sm text-gray-400">
                    Active until {format(new Date(profile.subscription_end_date), 'dd MMM yyyy')}
                  </p>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              <button className="rounded-3xl bg-red-600 px-6 py-3 font-semibold text-white shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-red-700">
                <Email className="mr-2" fontSize="small" />
                Message
              </button>
              <button className="rounded-3xl border border-gray-600 px-6 py-3 font-semibold text-white transition-all duration-300 hover:-translate-y-1 hover:bg-gray-700">
                <Share className="mr-2" fontSize="small" />
                Share Profile
              </button>
              <IconButton className="self-end">
                <MoreVert />
              </IconButton>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Sidebar */}
          <div className="space-y-6">
            <StatsCard stats={stats} />
            <GenreList genres={favoriteGenres} />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="overflow-hidden rounded-3xl shadow-2xl">
              <div className="bg-gray-800/95 backdrop-blur-sm">
                <StyledTabs
                  value={tabValue}
                  onChange={handleTabChange}
                  variant="fullWidth"
                  className="border-b border-gray-700"
                  TabIndicatorProps={{
                    style: { backgroundColor: '#dc2626', height: 2 },
                  }}
                >
                  <Tab label="Ratings & Reviews" className="py-4" />
                  <Tab label="My Lists" className="py-4" />
                  <Tab label="Activity" className="py-4" />
                </StyledTabs>

                <TabPanel value={tabValue} index={0}>
                  <RatingList ratings={ratings?.items || []} />
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                  <div className="p-12 text-center">
                    <h3 className="text-xl font-semibold text-gray-300">
                      Create Your Movie Collections
                    </h3>
                    <p className="mt-2 text-gray-400">
                      Organize movies into custom lists like "Best Action Movies", "Family
                      Favorites", or "Weekend Watchlist"
                    </p>
                  </div>
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                  <div className="p-12 text-center">
                    <h3 className="text-xl font-semibold text-gray-300">
                      Activity feed coming soon...
                    </h3>
                    <p className="mt-2 text-gray-400">See all user activities and interactions</p>
                  </div>
                </TabPanel>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
