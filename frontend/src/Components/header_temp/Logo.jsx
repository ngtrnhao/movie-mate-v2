import { Link } from 'react-router-dom';
const MovieMateLogo = () => {
  return (
    <Link to="/" className="flex items-center gap-2">
      <svg
        viewBox="0 0 24 24"
        className="size-8 text-red-600 transition-colors duration-150"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
        <path d="M7 2v20" />
        <path d="M17 2v20" />
        <path d="M2 12h20" />
        <path d="M2 7h5" />
        <path d="M2 17h5" />
        <path d="M17 17h5" />
        <path d="M17 7h5" />
      </svg>
      <span className="text-xl font-bold text-red-600 transition-colors duration-150">
        MovieMate
      </span>
    </Link>
  );
};
export default MovieMateLogo;
