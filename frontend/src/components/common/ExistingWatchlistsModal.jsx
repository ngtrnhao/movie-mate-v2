import { Dialog } from '@headlessui/react';
import { X, Plus } from 'lucide-react';
import { useWatchlistContext } from '../../context/WatchlistContext';

const ExistingWatchlistsModal = ({ isOpen, onClose, onSelect }) => {
  const { watchlists, loading, switchToCreateModal } = useWatchlistContext();

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto w-full max-w-sm rounded-lg bg-gray-800 p-6">
          <div className="mb-4 flex items-center justify-between">
            <Dialog.Title className="text-lg font-medium text-white">Add to Watchlist</Dialog.Title>
            <button onClick={onClose} className="text-gray-400 transition-colors hover:text-white">
              <X size={20} />
            </button>
          </div>

          {loading ? (
            <div className="py-8 text-center text-gray-400">Loading watchlists...</div>
          ) : watchlists.length === 0 ? (
            <div className="py-8 text-center">
              <p className="mb-4 text-gray-400">No watchlists found</p>
              <button
                onClick={switchToCreateModal}
                className="inline-flex items-center gap-2 rounded-md bg-red-500 px-4 py-2 text-white transition-colors hover:bg-red-600"
              >
                <Plus size={16} />
                Create New Watchlist
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <button
                onClick={switchToCreateModal}
                className="flex w-full items-center justify-center gap-2 rounded-md border-2 border-dashed border-gray-600 bg-gray-700 px-4 py-3 text-white transition-colors hover:border-red-500 hover:bg-gray-600"
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
                    className="flex w-full items-center justify-between rounded-md bg-gray-700 px-4 py-3 transition-colors hover:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <div className="flex flex-col items-start">
                      <span className="font-medium text-white">{watchlist.name}</span>
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
