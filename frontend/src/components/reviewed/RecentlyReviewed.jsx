import { Swiper, SwiperSlide } from 'swiper/react';
import { Pagination, Navigation } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';
import ReviewCard from './ReviewCard';
import mockReviews from './mockData';
import { motion } from 'framer-motion';

const RecentlyReviewed = () => {
  return (
    <section className="bg-gray-900 py-12 pl-14">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Recently Reviewed</h2>
          <p className="text-gray-400">Fresh perspectives from our community</p>
        </div>
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{
            scale: 1.08,
            boxShadow: '0 4px 24px 0 rgba(236, 72, 153, 0.25)',
            color: '#fff',
            backgroundColor: '#dc2626',
          }}
          whileTap={{ scale: 0.96, rotate: 0 }}
          className="mx-8 rounded-lg px-5 py-2 font-semibold text-pink-400 transition-colors duration-200 "
        >
          View All Reviews
        </motion.button>
      </div>
      {/* Swiper Carousel */}
      <Swiper
        modules={[Pagination, Navigation]}
        spaceBetween={24}
        slidesPerView={1}
        navigation
        pagination={{ el: '.custom-swiper-pagination', clickable: true }}
        breakpoints={{
          640: { slidesPerView: 2 },
          1024: { slidesPerView: 4 },
        }}
        className="pb-0"
      >
        {mockReviews.map(review => (
          <SwiperSlide key={review.id}>
            <ReviewCard review={review} />
          </SwiperSlide>
        ))}
      </Swiper>
      <div className="custom-swiper-pagination mt-4 flex justify-center" />
    </section>
  );
};

export default RecentlyReviewed;
