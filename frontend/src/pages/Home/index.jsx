import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
import FeaturedCategories from '../../components/categories/featured-categories';
import RecommendForYou from '../../components/recommend/recommend-for-you';
import RecentlyReviewed from '../../components/reviewed';
import TopRatedGrid from '../../components/movies/movie-grid/TopRatedGrid';
import FindSimilarMovies from '../../components/recommendation-tools/SimilarityFinder';
import TopGenreRecommendations from '../../components/movies/movie-grid/TopGenreRecommendations';
// import AdBannerTop from '../../components/ads/AdBannerTop';
import AdContent from '../../components/ads/AdContent';

const HomePage = () => {
  return (
    <div className="bg-gray-900">
      {/* Quảng cáo banner đầu trang
      <AdBannerTop /> */}

      <HeroBannerRecommendation />
      <MovieCarousel />

      {/* Quảng cáo nội dung giữa các section */}
      {/* <AdContent position="TOP" /> */}

      <RecommendForYou />
      <TopRatedGrid />
      <TopGenreRecommendations />

      {/* Quảng cáo nội dung giữa */}
      <AdContent position="MIDDLE" />

      <RecentlyReviewed />
      <FindSimilarMovies />
      <FeaturedCategories />

      {/* Quảng cáo nội dung cuối */}
      {/* <AdContent position="BOTTOM" /> */}
    </div>
  );
};

export default HomePage;
