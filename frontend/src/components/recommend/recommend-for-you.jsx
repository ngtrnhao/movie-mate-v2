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

const RecommendForYou = () => {
  return (
    <section className="mb-8 mt-12 w-full">
      <div className="ml-14">
        <h2 className="mb-6 text-3xl font-bold text-white">Recommend For You</h2>
        <div className="scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900 flex gap-6 overflow-x-auto pb-2">
          {mockRecommendations.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default RecommendForYou;
