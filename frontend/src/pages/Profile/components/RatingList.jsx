import { Box, Typography, Paper, Rating, Link, Grid } from '@mui/material';
import { styled } from '@mui/material/styles';
import { format } from 'date-fns';

const RatingCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  '&:last-child': {
    marginBottom: 0,
  },
}));

const RatingHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: theme.spacing(1),
}));

const MovieTitle = styled(Link)(({ theme }) => ({
  textDecoration: 'none',
  color: theme.palette.primary.main,
  fontWeight: 'bold',
  '&:hover': {
    textDecoration: 'underline',
  },
}));

const RatingDate = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

const RatingValue = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
}));

const RatingNumber = styled(Typography)(({ theme }) => ({
  fontWeight: 'bold',
  color: theme.palette.primary.main,
}));

const RatingList = ({ ratings }) => {
  if (!ratings || ratings.length === 0) {
    return (
      <Box p={3}>
        <Typography variant="body1" color="textSecondary" align="center">
          No ratings yet
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      {ratings.map(rating => (
        <Grid item xs={12} sm={6} key={rating.id}>
          <RatingCard elevation={1}>
            <RatingHeader>
              <MovieTitle component={Link} to={`/movies/${rating.movie.id}`}>
                {rating.movie.title}
              </MovieTitle>
              <RatingDate>{format(new Date(rating.created_at), 'MMM d, yyyy')}</RatingDate>
            </RatingHeader>
            <RatingValue>
              <Rating value={rating.rating} readOnly precision={0.5} />
              <RatingNumber>{rating.rating.toFixed(1)}</RatingNumber>
            </RatingValue>
          </RatingCard>
        </Grid>
      ))}
    </Grid>
  );
};

export default RatingList;
