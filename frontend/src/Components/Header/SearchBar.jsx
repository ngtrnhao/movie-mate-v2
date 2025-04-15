import { useState } from 'react';

const SearchBar = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    //Implement search logic
  };

  return (
    <div className="mx-4 max-w-2xl flex-1">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border px-4 py-2 focus:outline-none focus:ring-2"
          placeholder="Search for movies..."
        />
      </form>
    </div>
  );
};

export default SearchBar;
