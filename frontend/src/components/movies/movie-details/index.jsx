// components/movies/movie-details/index.jsx
import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getMovieDetails, getMovieCast, getSimilarMovies } from '../../../api/movieService';
import LoadingSpinner from '../../common/LoadingSpinner';
import InfoSection from './InfoSection';
import CastSection from './CastSection';
import ReviewSection from './ReviewSection';
import SimilarMovies from './SimilarMovies';

const MovieDetails = () => {
  const { movieId } = useParams();
  const [movie, setMovie] = useState(null);
  const [cast, setCast] = useState([]);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMovieData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch movie details
        const movieData = await getMovieDetails(movieId);
        console.log('Movie data:', movieData);
        setMovie(movieData?.data || movieData);

        // Fetch movie cast
        try {
          const castData = await getMovieCast(movieId);
          console.log('Cast data:', castData);
          setCast(castData?.data || []);
        } catch (castError) {
          console.error('Error fetching cast:', castError);
          setCast([]);
        }

        // Fetch similar movies based on genres
        if (movieData?.data?.genres?.length || movieData?.genres?.length) {
          try {
            const genres = movieData?.data?.genres || movieData?.genres || [];
            const similarData = await getSimilarMovies.data(movieId, genres, 6);
            console.log('Similar movies data:', similarData);
            setSimilarMovies(similarData?.data || []);
          } catch (similarError) {
            console.error('Error fetching similar movies:', similarError);
            setSimilarMovies([]);
          }
        }
      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError(err.error || 'Failed to fetch movie details');
      } finally {
        setLoading(false);
      }
    };

    if (movieId) {
      fetchMovieData();
    }
  }, [movieId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <h2 className="mb-2 text-2xl font-bold">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <div className="text-center text-white">
          <h2 className="mb-2 text-2xl font-bold">Movie Not Found</h2>
          <p>The requested movie could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <InfoSection movie={movie} />
      <CastSection cast={cast} />
      <ReviewSection movieId={movieId} />
      <SimilarMovies movies={similarMovies} />
    </div>
  );
};

export default MovieDetails;
