// components/movies/movie-details/index.jsx
import { useParams } from 'react-router-dom';
// import { useDispatch, useSelector } from 'react-redux';
import { motion } from 'framer-motion';
import { Play, Bookmark } from 'lucide-react';
import { Link } from 'react-router-dom';
// import { useEffect } from 'react';
// import { fetchMovieDetails } from '../../../store/slices/movieSlice';
import LoadingSpinner from '../../common/LoadingSpinner';

// Constants
const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';

// Mock data
const mockMovie = {
  id: 1,
  title: 'The Dark Knight',
  backdrop_path: '/b1Y8SUb12gPHCSSSNlbX4nB3IKy.jpg',
  poster_path: '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
  release_date: '2008-07-18',
  runtime: 152,
  vote_average: 8.5,
  overview:
    'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.',
  genres: [
    { id: 28, name: 'Action' },
    { id: 80, name: 'Crime' },
    { id: 18, name: 'Drama' },
  ],
  trailerUrl: 'https://www.youtube.com/watch?v=EXeTwQWrcwY',
  credits: {
    cast: [
      {
        cast_id: 1,
        name: 'Christian Bale',
        character: 'Bruce Wayne / Batman',
        profile_path: '/4D4P0UA0sImGoqfRz8RjQdKvdQf.jpg',
      },
      {
        cast_id: 2,
        name: 'Heath Ledger',
        character: 'Joker',
        profile_path: '/5YxXJtVzHhJzQJzQJzQJzQJzQJzQ.jpg',
      },
      // Add more cast if needed
    ],
  },
  recommendations: {
    results: [
      {
        id: 2,
        title: 'Inception',
        poster_path: '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
      },
      {
        id: 3,
        title: 'Interstellar',
        poster_path: '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
      },
    ],
  },
  reviews: {
    results: [
      {
        id: 1,
        author: 'John Doe',
        content: "One of the best movies ever made. Christopher Nolan's masterpiece.",
        created_at: '2024-01-01T00:00:00.000Z',
      },
      {
        id: 2,
        author: 'Jane Smith',
        content: "Heath Ledger's performance as the Joker is absolutely phenomenal.",
        created_at: '2024-01-02T00:00:00.000Z',
      },
      // Add more reviews if needed
    ],
  },
};

const MovieDetails = () => {
  const { movieId } = useParams();
  // const dispatch = useDispatch();

  // // Selectors from Redux store
  // const movie = useSelector((state) => state.movies.currentMovie);
  // const loading = useSelector((state) => state.movies.loading.currentMovie);
  // const error = useSelector((state) => state.movies.error.currentMovie);

  // useEffect(() => {
  //   dispatch(fetchMovieDetails(movieId));
  // }, [dispatch, movieId]);

  // Use mock data
  const movie = mockMovie;
  const loading = false;
  const error = null;

  if (loading) {
    return <LoadingSpinner />;
  }

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

  if (!movie) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero Section with Backdrop */}
      <div className="relative h-[60vh] w-full">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(${TMDB_IMAGE_BASE_URL}${movie.backdrop_path})`,
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent" />

        {/* Movie Info Overlay */}
        <div className="absolute inset-x-0 bottom-0 p-8">
          <div className="container mx-auto">
            <div className="flex gap-8">
              {/* Poster */}
              <motion.img
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                src={`${TMDB_IMAGE_BASE_URL}${movie.poster_path}`}
                alt={movie.title}
                className="h-[400px] w-[266px] rounded-lg shadow-2xl"
              />

              {/* Info */}
              <div className="flex-1 text-white">
                <h1 className="text-4xl font-bold">{movie.title}</h1>
                <div className="mt-2 flex items-center gap-4">
                  <span>{new Date(movie.release_date).getFullYear()}</span>
                  <span>•</span>
                  <span>{movie.runtime} min</span>
                  <span>•</span>
                  <div className="flex items-center">
                    <span className="text-yellow-400">★</span>
                    <span className="ml-1">{movie.vote_average.toFixed(1)}</span>
                  </div>
                </div>

                {/* Genres */}
                <div className="mt-4 flex gap-2">
                  {movie.genres?.map((genre) => (
                    <span
                      key={genre.id}
                      className="rounded-full bg-red-600/20 px-3 py-1 text-sm text-red-400"
                    >
                      {genre.name}
                    </span>
                  ))}
                </div>

                {/* Overview */}
                <p className="mt-6 text-lg text-gray-300">{movie.overview}</p>

                {/* Actions */}
                <div className="mt-8 flex gap-4">
                  <button
                    onClick={() => window.open(movie.trailerUrl, '_blank')}
                    className="flex items-center gap-2 rounded-md bg-red-600 px-6 py-3 text-white hover:bg-red-700"
                  >
                    <Play className="size-5" />
                    Watch Trailer
                  </button>
                  <button className="flex items-center gap-2 rounded-md border border-white/20 px-6 py-3 text-white hover:bg-white/10">
                    <Bookmark className="size-5" />
                    Add to Watchlist
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Sections: Cast, Recommendations, Reviews, etc. */}
      <div className="container mx-auto px-4 py-12">
        {/* Cast */}
        <section className="mb-12">
          <h2 className="mb-4 text-2xl font-bold text-white">Cast</h2>
          <div className="flex gap-6 overflow-x-auto">
            {movie.credits?.cast?.slice(0, 10).map((actor) => (
              <div key={actor.cast_id} className="flex flex-col items-center">
                <img
                  src={
                    actor.profile_path
                      ? `${TMDB_IMAGE_BASE_URL}${actor.profile_path}`
                      : '/default-avatar.png'
                  }
                  alt={actor.name}
                  className="mb-2 size-24 rounded-full object-cover"
                />
                <span className="text-sm text-white">{actor.name}</span>
                <span className="text-xs text-gray-400">{actor.character}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Recommendations */}
        <section className="mb-12">
          <h2 className="mb-4 text-2xl font-bold text-white">Recommended Movies</h2>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
            {movie.recommendations?.results?.slice(0, 6).map((rec) => (
              <Link key={rec.id} to={`/movies/${rec.id}`}>
                <img
                  src={
                    rec.poster_path
                      ? `${TMDB_IMAGE_BASE_URL}${rec.poster_path}`
                      : '/default-poster.png'
                  }
                  alt={rec.title}
                  className="h-48 w-full rounded-lg object-cover"
                />
                <div className="mt-2 text-sm text-white">{rec.title}</div>
              </Link>
            ))}
          </div>
        </section>

        {/* Reviews */}
        <section>
          <h2 className="mb-4 text-2xl font-bold text-white">Reviews</h2>
          <div className="space-y-6">
            {movie.reviews?.results?.slice(0, 3).map((review) => (
              <div key={review.id} className="rounded-lg bg-gray-800 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-semibold text-white">{review.author}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(review.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-gray-300">{review.content}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default MovieDetails;
