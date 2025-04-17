import SearchBar from './SearchBar';
import ThemeToggle from './ThemeToggle';
import Navigation from './Navigation';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-background relative transition-colors duration-150">
      <div className="mx-auto max-w-[1400px] px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
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

          {/* Center section */}
          <div className="flex flex-1 items-center justify-center">
            <div className="w-[400px]">
              <SearchBar />
            </div>
          </div>

          {/* Right section */}
          <div className="flex items-center space-x-6">
            <Navigation />
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
            <button className="bg-background inline-flex h-9 items-center justify-center rounded-md border border-red-600 px-4 text-sm font-medium text-red-600 transition-colors duration-150 hover:bg-red-600 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600 focus-visible:ring-offset-2">
              Sign In
            </button>
          </div>
        </div>
      </div>
      {/* Gradient line */}
      <div className="absolute inset-x-0 bottom-0 h-[2px]">
        <div className="size-full bg-gradient-to-r from-transparent via-red-600/40 to-transparent dark:via-red-500/50" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-600/20 to-transparent blur-[1px] dark:via-red-500/30" />
      </div>
    </header>
  );
};

export default Header;
