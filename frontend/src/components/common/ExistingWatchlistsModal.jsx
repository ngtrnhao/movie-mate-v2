import React from 'react';
import { Dialog } from '@headlessui/react';
import { X, Plus } from 'lucide-react';
import { useWatchlistContext } from '../../context/WatchlistContext';

const ExistingWatchlistsModal = ({ isOpen, onClose, onSelect }) => {
  const { watchlists, loading, switchToCreateModal } = useWatchlistContext();

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-sm rounded-lg bg-gray-800 p-6 w-full">
          <div className="flex justify-between items-center mb-4">
            <Dialog.Title className="text-lg font-medium text-white">Add to Watchlist</Dialog.Title>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>

          {loading ? (
            <div className="py-8 text-center text-gray-400">Loading watchlists...</div>
          ) : watchlists.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-gray-400 mb-4">No watchlists found</p>
              <button
                onClick={switchToCreateModal}
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
              >
                <Plus size={16} />
                Create New Watchlist
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <button
                onClick={switchToCreateModal}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-md text-white transition-colors border-2 border-dashed border-gray-600 hover:border-red-500"
              >
                <Plus size={16} />
                Create New Watchlist
              </button>

              <div className="space-y-2">
                {watchlists.map(watchlist => (
                  <button
                    key={watchlist.id}
                    onClick={() => onSelect(watchlist.id)}
                    disabled={loading}
                    className="w-full px-4 py-3 flex items-center justify-between bg-gray-700 hover:bg-gray-600 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex flex-col items-start">
                      <span className="text-white font-medium">{watchlist.name}</span>
                      <span className="text-sm text-gray-400">
                        {watchlist.items?.length || 0} movies
                      </span>
                    </div>
                    <Plus size={16} className="text-gray-400" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default ExistingWatchlistsModal;
