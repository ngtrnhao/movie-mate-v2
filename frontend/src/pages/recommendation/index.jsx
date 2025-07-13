import { useEffect } from 'react';
import useUserTracking from '../../hooks/useUserTracking';
import { RecommendationToolsHeader } from './RecommendationToolsHeader';
import SimilarityFinder from './SimilarityFinder';
import GenreExplorer from './GenreExplorer';
import MoodBasedRecommendations from './MoodBasedRecommendations';
import TrendingNow from './TrendingNow';

export default function Recommendation() {
  const { trackInteraction } = useUserTracking();

  // Track recommendation page view
  useEffect(() => {
    trackInteraction({
      action: 'page_view',
      metadata: {
        page: 'recommendation',
        timestamp: new Date().toISOString(),
      },
    });
  }, [trackInteraction]);

  return (
    <div className="min-h-screen bg-gray-900">
      <RecommendationToolsHeader />
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <SimilarityFinder showViewAllButton={false} />
          <GenreExplorer />
          <MoodBasedRecommendations />
        </div>
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <GenreExplorer />
          <TrendingNow />
        </div>
      </div>
    </div>
  );
}
