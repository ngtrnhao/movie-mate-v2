import { motion } from 'framer-motion';
import { Play, Bookmark } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';
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

const InfoSection = () => {
  const { t } = useTranslation('movies');
  const movie = mockMovie;
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero Section with Backdrop */}
      <div className="relative h-[60vh] w-full ">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(${TMDB_IMAGE_BASE_URL}${movie.backdrop_path})`,
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent" />

        {/* Movie Info Overlay */}
        <div className="absolute inset-x-0  pt-20">
          <div className="pt-30 container mx-auto">
            <div className="flex flex-col gap-6 px-2 sm:flex-col md:flex-row md:gap-8 md:px-0">
              {/* Poster */}
              <motion.img
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                src={`${TMDB_IMAGE_BASE_URL}${movie.poster_path}`}
                alt={movie.title}
                className="mx-auto h-[180px] w-[120px] rounded-lg shadow-2xl sm:h-[250px] sm:w-[167px] md:h-[400px] md:w-[267px] lg:h-[500px] lg:w-[333px]"
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

                <div className="mt-8 flex gap-4 pt-52">
                  <button
                    onClick={() => window.open(movie.trailerUrl, '_blank')}
                    className="flex items-center gap-1 rounded-md bg-red-600 px-4 py-3 text-white hover:bg-red-700"
                  >
                    <Play className="size-5" />
                    {t('details.watchTrailer')}
                  </button>
                  <button className="flex items-center gap-2 rounded-md border border-white/20 px-4 py-3 text-white hover:bg-white/10">
                    <Bookmark className="size-5" />
                    {t('details.addToWatchlist')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoSection;
