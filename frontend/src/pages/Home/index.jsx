import HeroBannerRecommendation from './HeroBanner';
import MovieCarousel from '../../components/movies/movie-carousel';
const HomePage = () => {
  return (
    <div className="bg-gray-900">
      <HeroBannerRecommendation />
      <MovieCarousel />
    </div>
  );
};

export default HomePage;
