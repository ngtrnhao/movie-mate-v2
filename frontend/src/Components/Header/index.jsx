import SearchBar from './SearchBar';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  return (
    <header className="flex items-center justify-between bg-white px-6 py-4 shadow-md transition-colors duration-200 dark:bg-gray-800">
      <div className="flex items-center">
        <SearchBar />
      </div>
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <button className="rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700">
          Sign In
        </button>
      </div>
    </header>
  );
};

export default Header;
