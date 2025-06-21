import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchProfile,
  fetchUserStats,
  // fetchWatchedMovies,
  fetchUserReviews,
  fetchUserRatings,
  fetchFavoriteGenres,
} from '../../store/slices/profileSlice';
import {
  selectProfile,
  selectProfileLoading,
  selectProfileError,
  selectUserStats,
  // selectWatchedMovies,
  selectUserReviews,
  selectUserRatings,
  selectFavoriteGenres,
} from '../../store/selectors/profileSelectors';
import {
  Box,
  Container,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Avatar,
  Button,
  Tabs,
  Tab,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import MovieList from './components/MovieList';
import ReviewList from './components/ReviewList';
import RatingList from './components/RatingList';
import StatsCard from './components/StatsCard';
import GenreList from './components/GenreList';
import { format } from 'date-fns';

const ProfileContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(4),
  paddingBottom: theme.spacing(4),
}));

const ProfileHeader = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(3),
}));

const ProfileAvatar = styled(Avatar)(({ theme }) => ({
  width: 120,
  height: 120,
  border: `4px solid ${theme.palette.primary.main}`,
}));

const ProfileInfo = styled(Box)(({ theme }) => ({
  flex: 1,
}));

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`profile-tabpanel-${index}`}
    aria-labelledby={`profile-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const Profile = () => {
  const { userId } = useParams();
  const dispatch = useDispatch();
  const [tabValue, setTabValue] = React.useState(0);

  const profile = useSelector(selectProfile);
  const loading = useSelector(selectProfileLoading);
  const error = useSelector(selectProfileError);
  const stats = useSelector(selectUserStats);
  // const watchedMovies = useSelector(selectWatchedMovies);
  const reviews = useSelector(selectUserReviews);
  const ratings = useSelector(selectUserRatings);
  const favoriteGenres = useSelector(selectFavoriteGenres);

  useEffect(() => {
    if (userId) {
      dispatch(fetchProfile(userId));
      dispatch(fetchUserStats(userId));
      // dispatch(fetchWatchedMovies(userId));
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
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!profile) {
    return (
      <Box p={3}>
        <Alert severity="info">Profile not found</Alert>
      </Box>
    );
  }

  return (
    <ProfileContainer maxWidth="lg">
      <ProfileHeader elevation={3}>
        <ProfileAvatar src={profile.avatar_url} alt={profile.username} />
        <ProfileInfo>
          <Typography variant="h4" gutterBottom>
            {profile.username}
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            {profile.bio || 'No bio available'}
          </Typography>
          {/* Subscription info */}
          {profile.user_type && profile.subscription_end_date && (
            <Box mt={2} p={2} bgcolor="#222b" borderRadius={2}>
              <Typography variant="subtitle1" color="primary">
                Gói hiện tại: <b>{profile.user_type.replace('prenium_', '').toUpperCase()}</b>
              </Typography>
              <Typography variant="body2">
                Hiệu lực từ:{' '}
                {profile.subscription_start_date
                  ? format(new Date(profile.subscription_start_date), 'dd/MM/yyyy')
                  : '--'}
              </Typography>
              <Typography variant="body2">
                Đến:{' '}
                {profile.subscription_end_date
                  ? format(new Date(profile.subscription_end_date), 'dd/MM/yyyy')
                  : '--'}
              </Typography>
            </Box>
          )}
          <Box display="flex" gap={2}>
            {/* <Button variant="contained" color="primary">
              Follow
            </Button> */}
            <Button variant="outlined">Message</Button>
          </Box>
        </ProfileInfo>
      </ProfileHeader>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <StatsCard stats={stats} />
          <Box mt={3}>
            <GenreList genres={favoriteGenres} />
          </Box>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              {/* <Tab label="Watched Movies" /> */}
              <Tab label="Reviews" />
              <Tab label="Ratings" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              {/* <MovieList movies={watchedMovies?.items || []} /> */}
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <ReviewList reviews={reviews?.items || []} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <RatingList ratings={ratings?.items || []} />
            </TabPanel>
          </Paper>
        </Grid>
      </Grid>
    </ProfileContainer>
  );
};

export default Profile;
