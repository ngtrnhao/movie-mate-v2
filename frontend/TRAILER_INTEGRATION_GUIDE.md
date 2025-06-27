# Trailer Integration Guide

## Overview

This guide explains how the MovieTrailerModal has been integrated with MovieCard components in the Movies page.

## Implementation Details

### 1. Components Used

- **MovieTrailerModal**: Modal component for displaying movie trailers
- **useTrailerModal**: Custom hook for managing trailer modal state
- **MovieCard**: Movie card component with trailer button
- **Actions**: Action buttons component within MovieCard

### 2. Integration Flow

#### Movies Page (`frontend/src/pages/Movies/index.jsx`)

```javascript
// Import required components and hooks
import MovieTrailerModal from '../../components/movies/movie-trailer/MovieTrailerModal';
import { useTrailerModal } from '../../hooks/useTrailerModal';

// Use the trailer modal hook
const { isTrailerOpen, modalMovie, modalTrailerUrl, closeTrailerModal, handleTrailerClick } = useTrailerModal();

// Enhanced trailer click handler
const handleMovieTrailerClick = useCallback(
  movie => {
    try {
      if (!movie?.trailers?.length) {
        console.warn('Movie has no trailers:', movie.title);
        return;
      }
      handleTrailerClick(movie);
    } catch (error) {
      console.error('Error opening trailer modal:', error);
    }
  },
  [handleTrailerClick]
);

// Pass handler to MovieCard
<MovieCard
  movie={movie}
  index={index}
  onTrailerClick={() => handleMovieTrailerClick(movie)}
/>

// Render the modal
<MovieTrailerModal
  isOpen={isTrailerOpen}
  onClose={closeTrailerModal}
  movie={modalMovie}
  trailerUrl={modalTrailerUrl}
/>
```

#### MovieCard Component (`frontend/src/components/movies/movie-card/index.jsx`)

```javascript
// Accept onTrailerClick prop
const MovieCard = memo(({ movie, onTrailerClick, index = 0 }) => {
  // Handle trailer click
  const handleTrailerClick = useCallback(() => {
    if (onTrailerClick && movieData.trailers?.length > 0) {
      onTrailerClick(movieData);
    }
  }, [onTrailerClick, movieData]);

  // Pass to Actions component
  <Actions movie={movieData} onlyMainButton onTrailerClick={handleTrailerClick} />;
});
```

#### Actions Component (`frontend/src/components/movies/movie-card/Actions.jsx`)

```javascript
// Handle trailer button click
const handleTrailerClick = e => {
  e.preventDefault();
  if (onTrailerClick && movie) {
    onTrailerClick(movie);
  }
};

// Render trailer button
<button
  onClick={handleTrailerClick}
  disabled={!movie?.trailers?.length}
  title={movie?.trailers?.length ? 'Watch Trailer' : 'No Trailer Available'}
>
  <Play size={16} />
  Watch Trailer
</button>;
```

### 3. useTrailerModal Hook (`frontend/src/hooks/useTrailerModal.js`)

The hook provides:

- **State management**: `isTrailerOpen`, `modalMovie`, `modalTrailerUrl`
- **Handlers**: `openTrailerModal`, `closeTrailerModal`, `handleTrailerClick`
- **Utilities**: `getTrailerUrl` for extracting YouTube URLs from movie data

### 4. MovieTrailerModal Component (`frontend/src/components/movies/movie-trailer/MovieTrailerModal.jsx`)

Features:

- **YouTube embed**: Automatically converts watch URLs to embed URLs
- **Loading states**: Shows loading spinner while iframe loads
- **Error handling**: Displays error messages if trailer fails to load
- **Keyboard support**: ESC key to close modal
- **Responsive design**: Works on all screen sizes
- **Accessibility**: Proper ARIA labels and focus management

## Usage

### For Users

1. Navigate to the Movies page
2. Find a movie card with a "Watch Trailer" button
3. Click the button to open the trailer modal
4. Watch the trailer in the embedded player
5. Click outside the modal or press ESC to close

### For Developers

1. Import `useTrailerModal` hook
2. Use the hook in your component
3. Pass `handleTrailerClick` to MovieCard components
4. Render `MovieTrailerModal` with the hook's state

## Data Requirements

Movies need to have a `trailers` array with the following structure:

```javascript
{
  trailers: [
    {
      type: 'TRAILER',
      youtube_key: 'dQw4w9WgXcQ',
    },
  ];
}
```

## Error Handling

The implementation includes several layers of error handling:

1. **MovieCard level**: Checks if movie has trailers before enabling button
2. **Hook level**: Validates movie and trailer URL before opening modal
3. **Modal level**: Handles iframe loading errors and displays user-friendly messages

## Performance Considerations

- **Lazy loading**: Trailer iframe only loads when modal opens
- **Memory management**: Iframe src is cleared when modal closes
- **Memoization**: Components use React.memo and useCallback for optimization
- **Caching**: Trailer URLs are generated efficiently using useCallback

## Future Enhancements

Potential improvements:

1. **Multiple trailers**: Support for selecting from multiple trailers
2. **Trailer quality**: Allow users to choose video quality
3. **Autoplay**: Option to autoplay trailers
4. **Fullscreen mode**: Enhanced fullscreen experience
5. **Subtitles**: Support for trailer subtitles
6. **Analytics**: Track trailer view metrics
