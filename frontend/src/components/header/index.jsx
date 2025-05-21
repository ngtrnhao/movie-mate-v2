import SearchBar from './SearchBar';
import ThemeToggle from './ThemeToggle';
import Navigation from './Navigation';
import MovieMateLogo from './Logo';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

const Header = () => {
  const { t } = useTranslation('common');
  const navigate = useNavigate();
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 z-50 w-full transition-all duration-300 ${
        isScrolled ? 'bg-gray-900/90 backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <div className="mx-auto max-w-[1400px] px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
          <MovieMateLogo />

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
            <button
              onClick={() => navigate('/login')}
              className="rounded-md border border-red-600 px-4 py-2 text-red-600 transition-colors hover:bg-red-600 hover:text-white"
            >
              {t('auth.signIn')}
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
