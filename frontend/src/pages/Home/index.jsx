import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
import FeaturedCategories from '../../components/categories/featured-categories';
import RecommendForYou from '../../components/recommend/recommend-for-you';
import RecentlyReviewed from '../../components/reviewed';
import TopRatedGrid from '../../components/movies/movie-grid/TopRatedGrid';
import FindSimilarMovies from '../../components/recommendation-tools/SimilarityFinder';
import TopGenreRecommendations from '../../components/movies/movie-grid/TopGenreRecommendations';
import {
  AdWrapper,
  AdBannerTop,
  AdContent,
  ScriptLoader,
  PremiumAdFreeMessage,
} from '../../components/ads';

const HomePage = () => {
  return (
    <div className="bg-gray-900">
      {/* Quảng cáo banner đầu trang - chỉ hiển thị cho non-premium users */}
      <AdWrapper>
        <AdBannerTop />
      </AdWrapper>

      {/* Thông báo ad-free cho premium users */}
      <PremiumAdFreeMessage />

      <HeroBannerRecommendation />
      <MovieCarousel />

      {/* Quảng cáo nội dung giữa các section - chỉ hiển thị cho non-premium users */}
      <AdWrapper>
        <AdContent position="TOP" />
      </AdWrapper>

      <RecommendForYou />
      <TopRatedGrid />
      <TopGenreRecommendations />

      {/* Quảng cáo nội dung giữa - chỉ hiển thị cho non-premium users */}
      <AdWrapper>
        <AdContent position="MIDDLE" />
        <ScriptLoader zoneId={9465780} />
      </AdWrapper>

      <RecentlyReviewed />
      <FindSimilarMovies />
      <FeaturedCategories />

      {/* Quảng cáo nội dung cuối - chỉ hiển thị cho non-premium users */}
      <AdWrapper>
        <AdContent position="BOTTOM" />
      </AdWrapper>
    </div>
  );
};

export default HomePage;
