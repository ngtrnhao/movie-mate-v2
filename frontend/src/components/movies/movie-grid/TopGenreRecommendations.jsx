import { useRef } from 'react';
import MovieCard from '../movie-card';
import { mockMovies } from '../../../mocks/movies';

const GENRES = [
  {
    id: 'action',
    title: 'Top Action Recommendations',
    description: 'Highest rated action movies',
  },
  {
    id: 'drama',
    title: 'Top Drama Recommendations',
    description: 'Highest rated drama movies',
  },
];

function getTopMoviesByGenre(genreId, limit = 10) {
  return mockMovies
    .filter((movie) => movie.genres.map((g) => g.toLowerCase()).includes(genreId))
    .sort((a, b) => b.vote_average - a.vote_average)
    .slice(0, limit);
}

const MOVIES_PER_VIEW = 5;
const CARD_WIDTH = 270; // px
const SCROLL_AMOUNT = MOVIES_PER_VIEW * CARD_WIDTH + (MOVIES_PER_VIEW - 1) * 28; // 28px là gap-7

const TopGenreRecommendations = () => {
  const scrollRefs = useRef({});

  const handleScroll = (genreId, direction) => {
    const ref = scrollRefs.current[genreId];
    if (ref) {
      ref.scrollBy({
        left: direction === 'left' ? -SCROLL_AMOUNT : SCROLL_AMOUNT,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="w-full py-8">
      {GENRES.map((genre) => {
        const movies = getTopMoviesByGenre(genre.id, 10);
        return (
          <section key={genre.id} className="mb-12 ml-14">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{genre.title}</h2>
                <p className="text-gray-500">{genre.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <button className="mx-2 font-semibold text-pink-400 transition-colors duration-200 hover:text-pink-600">
                  View All
                </button>
                <button
                  className="rounded-full p-2 text-gray-700 hover:bg-gray-200"
                  onClick={() => handleScroll(genre.id, 'left')}
                  aria-label="Scroll left"
                >
                  <svg
                    width="20"
                    height="20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                <button
                  className="rounded-full p-2 text-gray-700 hover:bg-gray-200"
                  onClick={() => handleScroll(genre.id, 'right')}
                  aria-label="Scroll right"
                >
                  <svg
                    width="20"
                    height="20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 6 15 12 9 18" />
                  </svg>
                </button>
              </div>
            </div>
            <div
              ref={(el) => (scrollRefs.current[genre.id] = el)}
              className="scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900 flex gap-7 overflow-x-auto pb-2"
              style={{ scrollBehavior: 'smooth' }}
            >
              {movies.map((movie) => (
                <div key={movie.id} className="min-w-[270px] max-w-[270px] shrink-0">
                  <MovieCard movie={movie} />
                </div>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
};

export default TopGenreRecommendations;
