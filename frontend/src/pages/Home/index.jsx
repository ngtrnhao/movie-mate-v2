import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
import FeaturedCategories from '../../components/categories/featured-categories';
import RecommendForYou from '../../components/recommend/recommend-for-you';

const HomePage = () => {
  return (
    <div className="bg-gray-900">
      <HeroBannerRecommendation />
      <MovieCarousel />
      <RecommendForYou />
      <FeaturedCategories />
    </div>
  );
};

export default HomePage;
