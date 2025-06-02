import { Grid, Card, CardMedia, CardContent, Typography, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Link } from 'react-router-dom';

const MovieCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'scale(1.02)',
  },
}));

const MovieLink = styled(Link)(({ theme }) => ({
  textDecoration: 'none',
  color: 'inherit',
}));

const MoviePoster = styled(CardMedia)(({ theme }) => ({
  height: 200,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
}));

const MovieTitle = styled(Typography)(({ theme }) => ({
  fontWeight: 'bold',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
}));

const MovieYear = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: '0.875rem',
}));

const MovieList = ({ movies }) => {
  if (!movies || movies.length === 0) {
    return (
      <Box p={3}>
        <Typography variant="body1" color="textSecondary" align="center">
          No movies watched yet
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {movies.map((movie) => (
        <Grid item xs={12} sm={6} md={4} key={movie.id}>
          <MovieLink to={`/movies/${movie.id}`}>
            <MovieCard>
              <MoviePoster
                image={
                  movie.poster_path
                    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
                    : '/placeholder.jpg'
                }
                title={movie.title}
              />
              <CardContent>
                <MovieTitle variant="h6" gutterBottom>
                  {movie.title}
                </MovieTitle>
                <MovieYear>{new Date(movie.release_date).getFullYear()}</MovieYear>
              </CardContent>
            </MovieCard>
          </MovieLink>
        </Grid>
      ))}
    </Grid>
  );
};

export default MovieList;
