// frontend/src/components/movies/movie-carousel/index.jsx
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Scrollbar, A11y } from 'swiper/modules';

// Import Swiper styles
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/scrollbar';

const mockMovies = [
  {
    id: 1,
    title: 'The Shawshank Redemption',
    poster_path: 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
    vote_average: 9.3,
  },
  {
    id: 2,
    title: 'The Godfather',
    poster_path: 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg',
    vote_average: 9.2,
  },
  {
    id: 3,
    title: 'The Dark Knight',
    poster_path: 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
    vote_average: 9.0,
  },
  {
    id: 4,
    title: 'Pulp Fiction',
    poster_path: 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg',
    vote_average: 8.9,
  },
  {
    id: 5,
    title: 'Forrest Gump',
    poster_path: 'https://image.tmdb.org/t/p/w500/arw2vcBveWOVZrFpxx9dtLykyb8.jpg',
    vote_average: 8.8,
  },
  {
    id: 6,
    title: 'Inception',
    poster_path: 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
    vote_average: 8.7,
  },
  {
    id: 7,
    title: 'Fight Club',
    poster_path: 'https://image.tmdb.org/t/p/w500/bptfVGEQuv6vDTIMVCHjJ9Dz8PX.jpg',
    vote_average: 8.8,
  },
  {
    id: 8,
    title: 'Interstellar',
    poster_path: 'https://image.tmdb.org/t/p/w500/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg',
    vote_average: 8.6,
  },
  {
    id: 9,
    title: 'The Matrix',
    poster_path: 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
    vote_average: 8.7,
  },
  {
    id: 10,
    title: 'Goodfellas',
    poster_path: 'https://image.tmdb.org/t/p/w500/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg',
    vote_average: 8.7,
  },
  {
    id: 11,
    title: 'The Lord of the Rings: The Return of the King',
    poster_path: 'https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg',
    vote_average: 8.9,
  },
  {
    id: 12,
    title: 'Se7en',
    poster_path: 'https://image.tmdb.org/t/p/w500/6yoghtyTpznpBik8EngEmJskVUO.jpg',
    vote_average: 8.6,
  },
];

const MovieCarousel = ({ title = 'Recommended Movies', movies = mockMovies }) => {
  return (
    <div className="relative -mt-32 w-full overflow-x-hidden pb-6">
      <style>{`
        .swiper-scrollbar {
          opacity: 0 !important;
          pointer-events: none !important;
          height: 0 !important;
        }
        .swiper:hover .swiper-button-prev,
        .swiper:hover .swiper-button-next {
          opacity: 1 !important;
          pointer-events: auto !important;
          background: rgba(0,0,0,0.6) !important;
          border-radius: 0 !important;
          width: 40px !important;
          height: 100% !important;
          transition: opacity 0.2s;
          top: 0 !important;
          margin-top: 0 !important;
        }
        .swiper-button-prev{
            left:0 !important;        
        }
        .swiper-button-next{
            right:0 !important;        
        }
        .swiper-button-prev,
        .swiper-button-next {
          opacity: 0 !important;
          pointer-events: none !important;
          background: #fff !important;
          transition: opacity 0.2s;
        }
        .swiper-button-disabled {
          display: none !important;
        }
        .swiper-button-prev::after,
        .swiper-button-next::after {
          color: #ef4444 !important;
          font-size: 28px !important;
        }
        .swiper-slide {
          transition: transform 0.7s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.5s;
        }
        .swiper-slide-active {
          transform: scale(1.04);
          z-index: 2;
          box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        }
        .swiper-slide img {
          transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .swiper-slide-active img {
          box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        }
      `}</style>
      <h2 className="mb-4 ml-14 text-3xl font-bold text-white">{title}</h2>
      <div className="relative ml-14">
        <Swiper
          modules={[Navigation, Scrollbar, A11y]}
          spaceBetween={12}
          slidesPerView={5.5}
          navigation
          slidesPerGroup={5.5}
          scrollbar={{ draggable: true }}
          speed={800}
          className="!px-0"
          breakpoints={{
            320: {
              slidesPerView: 2.2,
              slidesPerGroup: 2.2,
              spaceBetween: 8,
            },
            480: {
              slidesPerView: 3.2,
              slidesPerGroup: 3.2,
              spaceBetween: 10,
            },
            768: {
              slidesPerView: 4.2,
              slidesPerGroup: 4.2,
              spaceBetween: 12,
            },
            1024: {
              slidesPerView: 5.2,
              slidesPerGroup: 5.2,
              spaceBetween: 16,
            },
            1280: {
              slidesPerView: 5.5,
              slidesPerGroup: 5.5,
              spaceBetween: 20,
            },
          }}
        >
          {movies.map((movie) => (
            <SwiperSlide key={movie.id}>
              <div className="flex flex-col">
                <img
                  src={movie.poster_path}
                  alt={movie.title}
                  className="h-28 w-48 rounded-md object-cover shadow transition-transform hover:scale-105 sm:w-56 md:w-64 lg:h-40 lg:w-72 xl:h-44 xl:w-80"
                />
                <span className="mt-2 line-clamp-2 text-center text-sm text-white ">
                  {movie.title}
                </span>
              </div>
            </SwiperSlide>
          ))}
        </Swiper>
      </div>
    </div>
  );
};

export default MovieCarousel;
