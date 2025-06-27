import { memo, useState, useCallback, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

// Global image cache để tránh load lại
const imageCache = new Map();
const preloadQueue = new Set();

const Poster = memo(({ posterPath, title, priority = false }) => {
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState('');

  // Tối ưu useInView với rootMargin lớn hơn để preload sớm
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.01, // Giảm threshold để trigger sớm hơn
    rootMargin: '200px 0px', // Tăng margin để preload sớm hơn
    skip: false,
  });

  // Preload image khi inView hoặc priority
  useEffect(() => {
    if ((inView || priority) && posterPath && !currentSrc) {
      // Kiểm tra cache trước
      if (imageCache.has(posterPath)) {
        setCurrentSrc(posterPath);
        setIsImageLoaded(true);
        return;
      }

      // Preload image
      if (!preloadQueue.has(posterPath)) {
        preloadQueue.add(posterPath);

        const img = new Image();
        img.onload = () => {
          imageCache.set(posterPath, posterPath);
          preloadQueue.delete(posterPath);
          setCurrentSrc(posterPath);
          setIsImageLoaded(true);
        };
        img.onerror = () => {
          preloadQueue.delete(posterPath);
          setImageError(true);
        };
        img.src = posterPath;
      }
    }
  }, [inView, priority, posterPath, currentSrc]);

  const handleImageLoad = useCallback(() => {
    setIsImageLoaded(true);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
  }, []);

  // Memoize image className để tránh re-render
  const imageClassName = useMemo(() => {
    return `size-full object-cover transition-transform duration-300 will-change-transform group-hover:scale-105 ${
      isImageLoaded ? 'opacity-100' : 'opacity-0'
    }`;
  }, [isImageLoaded]);

  // Memoize placeholder để tránh re-render
  const placeholder = useMemo(
    () => (
      <div className="flex size-full items-center justify-center bg-gray-700">
        <span className="text-4xl text-gray-400">🎬</span>
      </div>
    ),
    []
  );

  // Memoize error placeholder
  const errorPlaceholder = useMemo(
    () => (
      <div className="flex size-full items-center justify-center bg-gray-600">
        <span className="text-2xl text-gray-400">📽️</span>
      </div>
    ),
    []
  );

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }} // Giảm duration để load nhanh hơn
      className="relative aspect-[2/3] w-full overflow-hidden"
    >
      {/* Poster Image - Render ngay lập tức nếu priority */}
      {(priority || inView) && currentSrc && (
        <img
          src={currentSrc}
          alt={title}
          loading={priority ? 'eager' : 'lazy'}
          onLoad={handleImageLoad}
          onError={handleImageError}
          className={imageClassName}
          fetchPriority={priority ? 'high' : 'auto'}
        />
      )}

      {/* Placeholder - Chỉ hiển thị khi chưa load xong */}
      {!isImageLoaded && !imageError && placeholder}

      {/* Error placeholder */}
      {imageError && errorPlaceholder}

      {/* Hover Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <div className="absolute inset-x-0 bottom-0 p-4">
          <h3 className="line-clamp-2 text-lg font-semibold text-white">{title}</h3>
        </div>
      </div>
    </motion.div>
  );
});

Poster.displayName = 'Poster';

export default Poster;
