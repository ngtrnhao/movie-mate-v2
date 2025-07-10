import { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { X } from 'lucide-react';

const CreateWatchlistModal = ({ isOpen, onClose, onSubmit, loading }) => {
  const [name, setName] = useState('');

  const handleSubmit = e => {
    e.preventDefault();
    onSubmit(name);
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto w-full max-w-sm rounded-lg bg-gray-800 p-6">
          <div className="mb-4 flex items-center justify-between">
            <Dialog.Title className="text-lg font-medium text-white">
              Create New Watchlist
            </Dialog.Title>
            <button onClick={onClose} className="text-gray-400 transition-colors hover:text-white">
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="mb-1 block text-sm font-medium text-gray-300">
                Watchlist Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Enter watchlist name"
                required
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !name.trim()}
                className="rounded-md bg-red-500 px-4 py-2 text-white transition-colors hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default CreateWatchlistModal;
