import { useState, lazy, Suspense } from 'react';
import { MessageCircle, Star } from 'lucide-react';

// Lazy load the tab components
const RatingTab = lazy(() => import('./RatingTab'));
const CommentTab = lazy(() => import('./CommentTab'));

const MovieReviewSection = ({ movieId }) => {
  const [activeTab, setActiveTab] = useState('ratings');

  const tabs = [
    { id: 'ratings', label: 'Đánh giá', icon: Star },
    { id: 'comments', label: 'Bình luận', icon: MessageCircle },
  ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          {tabs.map(tab => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-yellow-500 text-black'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <IconComponent size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'ratings' && (
          <Suspense
            fallback={<div className="text-center text-gray-400">Đang tải đánh giá...</div>}
          >
            <RatingTab movieId={movieId} />
          </Suspense>
        )}
        {activeTab === 'comments' && (
          <Suspense
            fallback={<div className="text-center text-gray-400">Đang tải bình luận...</div>}
          >
            <CommentTab movieId={movieId} />
          </Suspense>
        )}
      </div>
    </div>
  );
};

export default MovieReviewSection;
