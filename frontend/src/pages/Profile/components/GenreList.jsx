import { Paper, Typography, Box, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';

const GenreCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  height: '100%',
}));

const GenreChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
}));

const GenreList = ({ genres }) => {
  if (!genres || genres.length === 0) {
    return (
      <GenreCard elevation={3}>
        <Typography variant="h6" gutterBottom>
          Favorite Genres
        </Typography>
        <Typography variant="body2" color="textSecondary">
          No favorite genres yet
        </Typography>
      </GenreCard>
    );
  }

  return (
    <GenreCard elevation={3}>
      <Typography variant="h6" gutterBottom>
        Favorite Genres
      </Typography>
      <Box display="flex" flexWrap="wrap" gap={1}>
        {genres.map(genre => (
          <GenreChip key={genre.id} label={genre.name} size="small" />
        ))}
      </Box>
    </GenreCard>
  );
};

export default GenreList;
