const MovieCard = ({ movie }) => (
  <div className="relative flex flex-col overflow-hidden rounded-lg bg-gray-100 shadow dark:bg-gray-800">
    {/* Badge */}
    {movie.adult && (
      <span className="absolute right-3 top-3 z-10 rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold text-white">
        R
      </span>
    )}
    {/* Poster */}
    <div className="flex min-h-[220px] flex-1 items-center justify-center bg-gray-200">
      {movie.poster_path ? (
        <img
          src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
          alt={movie.title}
          className="size-full object-cover"
        />
      ) : (
        <span className="text-4xl text-gray-400">🖼️</span>
      )}
    </div>
    {/* Info */}
    <div className="bg-[#1e293b] p-4">
      <h3 className="truncate text-lg font-semibold text-white">{movie.title}</h3>
      <div className="mt-1 flex items-center gap-2 text-sm text-gray-400">
        <span>{movie.release_date?.slice(0, 4)}</span>
      </div>
      <div className="mt-1 flex items-center gap-1 text-base text-yellow-400">
        <span>★</span>
        <span>{movie.vote_average}</span>
        <span className="text-xs text-gray-400">
          ({movie.vote_count && (movie.vote_count / 1e6).toFixed(1) + 'M'})
        </span>
      </div>
    </div>
  </div>
);
export default MovieCard;
