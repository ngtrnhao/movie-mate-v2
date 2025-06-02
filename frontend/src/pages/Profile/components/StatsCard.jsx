import { Paper, Typography, Grid, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import MovieIcon from '@mui/icons-material/Movie';
import RateReviewIcon from '@mui/icons-material/RateReview';
import StarIcon from '@mui/icons-material/Star';
import PeopleIcon from '@mui/icons-material/People';

const StatsCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  height: '100%',
}));

const StatItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: theme.spacing(2),
}));

const StatIcon = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(1),
  color: theme.palette.primary.main,
}));

const StatValue = styled(Typography)(({ theme }) => ({
  fontSize: '1.5rem',
  fontWeight: 'bold',
  color: theme.palette.text.primary,
}));

const StatLabel = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

const StatsCardComponent = ({ stats }) => {
  if (!stats) return null;

  return (
    <StatsCard elevation={3}>
      <Typography variant="h6" gutterBottom>
        Statistics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <StatItem>
            <StatIcon>
              <MovieIcon fontSize="large" />
            </StatIcon>
            <StatValue>{stats.watched_movies_count || 0}</StatValue>
            <StatLabel>Watched Movies</StatLabel>
          </StatItem>
        </Grid>
        <Grid item xs={6}>
          <StatItem>
            <StatIcon>
              <RateReviewIcon fontSize="large" />
            </StatIcon>
            <StatValue>{stats.reviews_count || 0}</StatValue>
            <StatLabel>Reviews</StatLabel>
          </StatItem>
        </Grid>
        <Grid item xs={6}>
          <StatItem>
            <StatIcon>
              <StarIcon fontSize="large" />
            </StatIcon>
            <StatValue>{stats.ratings_count || 0}</StatValue>
            <StatLabel>Ratings</StatLabel>
          </StatItem>
        </Grid>
        <Grid item xs={6}>
          <StatItem>
            <StatIcon>
              <PeopleIcon fontSize="large" />
            </StatIcon>
            <StatValue>{stats.followers_count || 0}</StatValue>
            <StatLabel>Followers</StatLabel>
          </StatItem>
        </Grid>
      </Grid>
    </StatsCard>
  );
};

export default StatsCardComponent;
