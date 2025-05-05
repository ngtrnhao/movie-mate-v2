import MovieCard from '../movie-card/MovieCard';

const MovieGrid = ({ movies, loading, error }) => {
  if (loading) return <div className="text-center text-white">Loading...</div>;
  if (error) return <div className="text-center text-red-500">{error}</div>;
  if (!movies.length) return <div className="text-center text-gray-400">No movies found.</div>;

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
      {movies.map((movie) => (
        <MovieCard key={movie.id} movie={movie} />
      ))}
    </div>
  );
};
export default MovieGrid;
