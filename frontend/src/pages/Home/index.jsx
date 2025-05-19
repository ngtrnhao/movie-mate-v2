import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
import FeaturedCategories from '../../components/categories/featured-categories';
import RecommendForYou from '../../components/recommend/recommend-for-you';
import TopRatedGrid from '../../components/movies/movie-grid/TopRatedGrid';

const HomePage = () => {
  return (
    <div className="bg-gray-900">
      <HeroBannerRecommendation />
      <MovieCarousel />
      <RecommendForYou />
      <TopRatedGrid />
      <FeaturedCategories />
    </div>
  );
};

export default HomePage;
