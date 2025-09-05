import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useDebounce } from '../../hooks/useDebounce';
import { getSearchSuggestions } from '../../api/movieService';
import { Search, Clock, TrendingUp, X } from 'lucide-react';
import useUserTracking from '../../hooks/useUserTracking';

const SearchBar = () => {
  const { t, currentLanguage } = useTranslation('common');
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const { trackInteraction, trackSearch } = useUserTracking();

  // Debounce search query to avoid too many API calls
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Get recent searches from localStorage
  const getRecentSearches = () => {
    try {
      const recent = localStorage.getItem('recentSearches');
      return recent ? JSON.parse(recent) : [];
    } catch {
      return [];
    }
  };

  const [recentSearches, setRecentSearches] = useState(getRecentSearches());

  // Save search to recent searches
  const saveToRecentSearches = query => {
    if (!query.trim()) return;

    const updated = [query, ...recentSearches.filter(item => item !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  };

  // Fetch suggestions when debounced query changes
  useEffect(() => {
    const fetchSuggestions = async () => {
      console.log(
        'Debug - debouncedQuery:',
        debouncedQuery,
        'length:',
        debouncedQuery.length,
        'currentLanguage:',
        currentLanguage
      );
      if (debouncedQuery.length >= 2) {
        setIsLoading(true);
        try {
          console.log(
            'Debug - Calling getSearchSuggestions with:',
            debouncedQuery,
            currentLanguage
          );
          const result = await getSearchSuggestions(debouncedQuery, currentLanguage, 8);
          console.log('Debug - Suggestions result:', result);
          setSuggestions(result.data || []);
        } catch (error) {
          console.error('Error fetching suggestions:', error);
          setSuggestions([]);
        } finally {
          setIsLoading(false);
        }
      } else {
        setSuggestions([]);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery, currentLanguage]);

  // Handle search submission
  const handleSearch = (e, query = searchQuery) => {
    e?.preventDefault();
    const searchTerm = query.trim();

    if (searchTerm) {
      // Track search interaction using specific trackSearch method
      trackSearch(searchTerm, []); // Empty array for resultIds, will be populated when results load

      saveToRecentSearches(searchTerm);
      setShowSuggestions(false);
      setSelectedIndex(-1);
      // Update URL and navigate to movies page with search query
      const currentPath = window.location.pathname;
      const isMoviesPage = currentPath === '/movies';

      if (isMoviesPage) {
        // If already on movies page, just update the URL
        const searchParams = new URLSearchParams(window.location.search);
        searchParams.set('q', searchTerm);
        navigate(`${currentPath}?${searchParams.toString()}`, { replace: true });
      } else {
        // Navigate to movies page with search query
        navigate(`/movies?q=${encodeURIComponent(searchTerm)}`);
      }
    }
  };

  // Handle input changes
  const handleInputChange = e => {
    const value = e.target.value;
    console.log('Debug - Input change:', value, 'length:', value.length);
    setSearchQuery(value);
    setSelectedIndex(-1);

    // If on movies page and input is cleared, reset search
    if (!value.trim() && window.location.pathname === '/movies') {
      const searchParams = new URLSearchParams(window.location.search);
      searchParams.delete('q');
      navigate(`/movies?${searchParams.toString()}`, { replace: true });
    }

    setShowSuggestions(value.length >= 2);
  };

  // Handle clear search
  const handleClearSearch = () => {
    setSearchQuery('');
    setShowSuggestions(false);
    setSelectedIndex(-1);

    // If on movies page, reset search
    if (window.location.pathname === '/movies') {
      const searchParams = new URLSearchParams(window.location.search);
      searchParams.delete('q');
      navigate(`/movies?${searchParams.toString()}`, { replace: true });
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const maxIndex = Math.max(suggestions.length - 1, recentSearches.length - 1);
      setSelectedIndex(prev => (prev < maxIndex ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const maxIndex = Math.max(suggestions.length - 1, recentSearches.length - 1);
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : maxIndex));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0) {
        if (searchQuery.length >= 2 && selectedIndex < suggestions.length) {
          // Select from suggestions - navigate to movie details
          const selectedSuggestion = suggestions[selectedIndex];
          setShowSuggestions(false);
          setSelectedIndex(-1);
          navigate(`/movies/${selectedSuggestion.id}`);
        } else if (searchQuery.length < 2 && selectedIndex < recentSearches.length) {
          // Select from recent searches - do search
          handleSearch(e, recentSearches[selectedIndex]);
        }
      } else {
        handleSearch(e);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedIndex(-1);
      searchInputRef.current?.blur();
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = suggestion => {
    if (typeof suggestion === 'string') {
      // If it's a string (from recent searches), do search
      setSearchQuery(suggestion);
      handleSearch(null, suggestion);
    } else {
      // If it's a movie suggestion, navigate to movie details
      setShowSuggestions(false);
      setSelectedIndex(-1);
      navigate(`/movies/${suggestion.id}`);
    }
  };

  // Handle input focus
  const handleInputFocus = () => {
    if (searchQuery.length >= 2 || recentSearches.length > 0) {
      setShowSuggestions(true);
    }
  };

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = event => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        !searchInputRef.current?.contains(event.target)
      ) {
        setShowSuggestions(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Clear recent searches
  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recentSearches');
  };

  return (
    <form onSubmit={handleSearch} className="relative w-full">
      {/* Search Input */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
        <input
          ref={searchInputRef}
          type="text"
          value={searchQuery}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleInputFocus}
          className="h-10 w-full rounded-lg border-0 bg-gray-800/50 px-10 text-sm text-white transition-all duration-200 placeholder:text-gray-400 focus:bg-gray-800/80 focus:outline-none focus:ring-2 focus:ring-red-500/50"
          placeholder={t('search.placeholder') || 'Search movies...'}
          autoComplete="off"
        />

        {/* Clear button */}
        {searchQuery && !isLoading && (
          <button
            type="button"
            onClick={handleClearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
          >
            <X className="size-4" />
          </button>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="size-4 animate-spin rounded-full border-2 border-gray-400 border-t-red-500"></div>
          </div>
        )}
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <div
          ref={suggestionsRef}
          className="absolute inset-x-0 top-full z-50 mt-1 max-h-96 overflow-y-auto rounded-lg border border-gray-700 bg-gray-800/95 shadow-xl backdrop-blur-sm"
        >
          {/* Recent Searches */}
          {searchQuery.length < 2 && recentSearches.length > 0 && (
            <div className="border-b border-gray-700 p-2">
              <div className="mb-2 flex items-center justify-between">
                <span className="flex items-center gap-1 text-xs font-medium text-gray-400">
                  <Clock className="size-3" />
                  {t('search.recent') || 'Recent searches'}
                </span>
                <button
                  type="button"
                  onClick={clearRecentSearches}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  {t('search.clear') || 'Clear'}
                </button>
              </div>
              {recentSearches.map((search, index) => (
                <button
                  key={`recent-${index}`}
                  type="button"
                  onClick={() => handleSuggestionClick(search)}
                  className={`w-full rounded px-3 py-2 text-left text-sm text-gray-300 transition-colors hover:bg-gray-700/50 ${
                    selectedIndex === index ? 'bg-gray-700/50' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Clock className="size-3 text-gray-500" />
                    {search}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Movie Suggestions */}
          {searchQuery.length >= 2 && !isLoading && (
            <div className="p-2">
              <div className="mb-2 flex items-center gap-1">
                <TrendingUp className="size-3 text-gray-400" />
                <span className="text-xs font-medium text-gray-400">
                  {t('search.suggestions') || 'Suggestions'}
                </span>
              </div>
              {suggestions.length > 0 ? (
                suggestions.map((movie, index) => (
                  <button
                    key={`suggestion-${movie.id}`}
                    type="button"
                    onClick={() => handleSuggestionClick(movie)}
                    className={`w-full rounded p-3 text-left transition-colors hover:bg-gray-700/50 ${
                      selectedIndex === index ? 'bg-gray-700/50' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {movie.poster_url ? (
                        <img
                          src={movie.poster_url}
                          alt={movie.title}
                          className="h-12 w-8 rounded object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="flex h-12 w-8 items-center justify-center rounded bg-gray-700">
                          <span className="text-xs text-gray-400">No image</span>
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-white">{movie.title}</p>
                        {movie.title_en && movie.title_vi && movie.title !== movie.title_en && (
                          <p className="truncate text-xs text-gray-400">
                            {currentLanguage === 'vi' ? movie.title_en : movie.title_vi}
                          </p>
                        )}
                        {movie.year && (
                          <p className="text-xs text-gray-500">
                            {movie.year}
                            {movie.rating?.imdb && ` • IMDb ${movie.rating.imdb}`}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="px-3 py-2 text-sm text-gray-400">
                  {t('search.no_results') || 'No results found'}
                </div>
              )}
            </div>
          )}

          {/* No results message */}
          {searchQuery.length >= 2 && !isLoading && suggestions.length === 0 && (
            <div className="p-4 text-center text-sm text-gray-400">
              {t('search.noResults') || 'No movies found'}
            </div>
          )}
        </div>
      )}
    </form>
  );
};

export default SearchBar;
