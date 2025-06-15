import { Box, Typography, Paper, Rating, Link } from '@mui/material';
import { styled } from '@mui/material/styles';
import { format } from 'date-fns';

const ReviewCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  '&:last-child': {
    marginBottom: 0,
  },
}));

const ReviewHeader = styled(Box)(({ theme }) => ({
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

const ReviewDate = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

const ReviewContent = styled(Typography)(({ theme }) => ({
  marginTop: theme.spacing(1),
  whiteSpace: 'pre-wrap',
}));

const ReviewList = ({ reviews }) => {
  if (!reviews || reviews.length === 0) {
    return (
      <Box p={3}>
        <Typography variant="body1" color="textSecondary" align="center">
          No reviews yet
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {reviews.map(review => (
        <ReviewCard key={review.id} elevation={1}>
          <ReviewHeader>
            <MovieTitle component={Link} to={`/movies/${review.movie.id}`}>
              {review.movie.title}
            </MovieTitle>
            <ReviewDate>{format(new Date(review.created_at), 'MMM d, yyyy')}</ReviewDate>
          </ReviewHeader>
          <Rating value={review.rating} readOnly precision={0.5} />
          <ReviewContent variant="body1">{review.content}</ReviewContent>
        </ReviewCard>
      ))}
    </Box>
  );
};

export default ReviewList;
