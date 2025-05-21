import { useRef } from 'react';
import MovieCard from '../movies/movie-card';

const mockRecommendations = [
  {
    id: 101,
    title: 'Inception',
    poster_path: 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.7,
    match: 97,
    release_date: '2019-10-04',
    recommendReason: 'Because you liked Sci-Fi thrillers',
  },
  {
    id: 102,
    title: 'Interstellar',
    poster_path: 'https://image.tmdb.org/t/p/w500/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg',
    vote_average: 8.6,
    match: 95,
    release_date: '2019-10-04',
    recommendReason: 'Based on your interest in space adventures',
  },
  {
    id: 103,
    title: 'Parasite',
    poster_path: 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg',
    vote_average: 8.5,
    match: 92,
    release_date: '2019-10-04',
    recommendReason: 'Because you watched Oscar-winning movies',
  },
  {
    id: 104,
    title: 'Joker',
    poster_path: 'https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg',
    vote_average: 8.4,
    match: 90,
    release_date: '2019-10-04',
    recommendReason: 'Recommended for psychological drama fans',
  },
  {
    id: 105,
    title: 'Avengers: Endgame',
    poster_path: 'https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg',
    vote_average: 8.4,
    match: 89,
    release_date: '2019-10-04',
    recommendReason: 'Because you like superhero blockbusters',
  },
];

const MOVIES_PER_VIEW = 5;
const CARD_WIDTH = 270; // px (desktop)
const SCROLL_AMOUNT = MOVIES_PER_VIEW * CARD_WIDTH + (MOVIES_PER_VIEW - 1) * 28;

const RecommendForYou = () => {
  const scrollRef = useRef(null);

  const handleScroll = (direction) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -SCROLL_AMOUNT : SCROLL_AMOUNT,
        behavior: 'smooth',
      });
    }
  };

  return (
    <section className="mb-8 mt-12 w-full">
      <div className="ml-2 sm:ml-8 md:ml-14">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Recommend For You</h2>
          <div className="flex items-center gap-2">
            <button
              className="rounded-full p-2 text-gray-700 hover:bg-gray-200"
              onClick={() => handleScroll('left')}
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
              onClick={() => handleScroll('right')}
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
          ref={scrollRef}
          className="scrollbar-none md:scrollbar-thin md:scrollbar-thumb-gray-700 md:scrollbar-track-gray-900 flex gap-4 overflow-x-auto pb-2 md:gap-6 lg:gap-7"
          style={{ scrollBehavior: 'smooth' }}
        >
          {mockRecommendations.map((movie) => (
            <div
              key={movie.id}
              className="min-w-[70vw] max-w-[70vw] shrink-0 sm:min-w-[40vw] sm:max-w-[40vw] md:min-w-[210px] md:max-w-[210px] lg:min-w-[240px] lg:max-w-[240px] xl:min-w-[270px] xl:max-w-[270px]"
            >
              <MovieCard movie={movie} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default RecommendForYou;
