import React, { createContext, useContext, useState, useCallback } from 'react';
import { useWatchlist } from '../hooks/useWatchlist';
import { toast } from 'react-toastify';
import CreateWatchlistModal from '../components/common/CreateWatchlistModal';
import ExistingWatchlistsModal from '../components/common/ExistingWatchlistsModal';

const WatchlistContext = createContext();

export const useWatchlistContext = () => {
  const context = useContext(WatchlistContext);
  if (!context) {
    throw new Error('useWatchlistContext must be used within a WatchlistProvider');
  }
  return context;
};

export const WatchlistProvider = ({ children }) => {
  const { watchlists, addToWatchlist, addMovieToExistingWatchlist, removeFromWatchlist, loading } =
    useWatchlist();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isExistingModalOpen, setIsExistingModalOpen] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [previousPath, setPreviousPath] = useState(null);

  const openCreateModal = useCallback((movieId, movieData, returnPath) => {
    setSelectedMovie({ id: movieId, data: movieData });
    setPreviousPath(returnPath);
    setIsCreateModalOpen(true);
    setIsExistingModalOpen(false);
  }, []);

  const openExistingModal = useCallback((movieId, movieData, returnPath) => {
    setSelectedMovie({ id: movieId, data: movieData });
    setPreviousPath(returnPath);
    setIsExistingModalOpen(true);
    setIsCreateModalOpen(false);
  }, []);

  const handleCreateWatchlist = useCallback(
    async name => {
      if (!selectedMovie) return;

      const result = await addToWatchlist({
        movieId: selectedMovie.id,
        movieData: selectedMovie.data,
        name,
        status: 'PLANNED',
      });

      if (result.success) {
        toast.success('Watchlist created successfully!');
        setIsCreateModalOpen(false);
        if (previousPath) {
          window.history.pushState(null, '', previousPath);
        }
      } else {
        toast.error(result.error || 'Failed to create watchlist');
      }
    },
    [addToWatchlist, selectedMovie, previousPath]
  );

  const handleAddToExistingWatchlist = useCallback(
    async watchlistId => {
      if (!selectedMovie) return;

      const result = await addMovieToExistingWatchlist(watchlistId, selectedMovie.id);

      if (result.success) {
        toast.success('Movie added to watchlist!');
        setIsExistingModalOpen(false);
        if (previousPath) {
          window.history.pushState(null, '', previousPath);
        }
      } else {
        toast.error(result.error || 'Failed to add movie to watchlist');
      }
    },
    [addMovieToExistingWatchlist, selectedMovie, previousPath]
  );

  const handleRemoveFromWatchlist = useCallback(
    async (watchlistId, movieId) => {
      const result = await removeFromWatchlist(watchlistId, movieId);

      if (result.success) {
        toast.success('Movie removed from watchlist!');
      } else {
        toast.error(result.error || 'Failed to remove movie from watchlist');
      }

      return result;
    },
    [removeFromWatchlist]
  );

  const isInWatchlist = useCallback(
    movieId => {
      return watchlists.some(watchlist =>
        watchlist.items.some(item => (item.movie_data?.id || item.movie?.id) === movieId)
      );
    },
    [watchlists]
  );

  const switchToCreateModal = useCallback(() => {
    setIsExistingModalOpen(false);
    setIsCreateModalOpen(true);
  }, []);

  const value = {
    watchlists,
    loading,
    isCreateModalOpen,
    isExistingModalOpen,
    selectedMovie,
    openCreateModal,
    openExistingModal,
    handleCreateWatchlist,
    handleAddToExistingWatchlist,
    handleRemoveFromWatchlist,
    isInWatchlist,
    setIsCreateModalOpen,
    setIsExistingModalOpen,
    switchToCreateModal,
  };

  return (
    <WatchlistContext.Provider value={value}>
      {children}
      <CreateWatchlistModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setSelectedMovie(null);
        }}
        onSubmit={handleCreateWatchlist}
        loading={loading}
      />
      <ExistingWatchlistsModal
        isOpen={isExistingModalOpen}
        onClose={() => {
          setIsExistingModalOpen(false);
          setSelectedMovie(null);
        }}
        onSelect={handleAddToExistingWatchlist}
        watchlists={watchlists}
        loading={loading}
      />
    </WatchlistContext.Provider>
  );
};
