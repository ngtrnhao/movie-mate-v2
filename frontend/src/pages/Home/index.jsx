import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
import FeaturedCategories from '../../components/categories/featured-categories';
import RecommendForYou from '../../components/recommend/recommend-for-you';
import CollaborativeRecommendations from '../../components/recommend/CollaborativeRecommendations';
import DemographicRecommendations from '../../components/recommend/DemographicRecommendations';
import ContentBasedRecommendations from '../../components/recommend/ContentBasedRecommendations';
import MovieBuzzSection from '../../components/reviewed/MovieBuzzSection';
import TopRatedGrid from '../../components/movies/movie-grid/TopRatedGrid';
import FindSimilarMovies from '../../components/recommendation-tools/SimilarityFinder';
import TopGenreRecommendations from '../../components/movies/movie-grid/TopGenreRecommendations';
import useUserTracking from '../../hooks/useUserTracking';
import { useEffect } from 'react';

const HomePage = () => {
  const { trackInteraction } = useUserTracking();

  // Track home page view
  useEffect(() => {
    trackInteraction({
      action: 'page_view',
      metadata: {
        page: 'home',
        timestamp: new Date().toISOString(),
      },
    });
  }, [trackInteraction]);

  return (
    <div className="bg-gray-900">
      {/* Quảng cáo banner đầu trang - chỉ hiển thị cho non-premium users */}
      {/* <AdWrapper>
        <AdBannerTop />
      </AdWrapper> */}

      {/* Thông báo ad-free cho premium users */}
      {/* <PremiumAdFreeMessage /> */}

      <HeroBannerRecommendation />
      <MovieCarousel />

      {/* Quảng cáo nội dung giữa các section - chỉ hiển thị cho non-premium users */}
      {/* <AdWrapper>
        <AdContent position="TOP" />
      </AdWrapper> */}

      {/* Hybrid Recommendations (Personalized) */}
      <RecommendForYou />

      {/* Individual Algorithm Recommendations */}
      <CollaborativeRecommendations />
      <DemographicRecommendations />
      <ContentBasedRecommendations />

      <TopRatedGrid />
      <TopGenreRecommendations />

      {/* Quảng cáo nội dung giữa - chỉ hiển thị cho non-premium users */}
      {/* <AdWrapper>
        <AdContent position="MIDDLE" />
        <ScriptLoader zoneId={9465780} />
      </AdWrapper> */}

      <MovieBuzzSection />
      <FindSimilarMovies />
      <FeaturedCategories />

      {/* Quảng cáo nội dung cuối - chỉ hiển thị cho non-premium users */}
      {/* <AdWrapper>
        <AdContent position="BOTTOM" />
      </AdWrapper> */}
    </div>
  );
};

export default HomePage;
