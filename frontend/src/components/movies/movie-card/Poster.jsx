import { memo, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

const Poster = memo(({ posterPath, title }) => {
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const handleImageLoad = useCallback(() => {
    setIsImageLoaded(true);
  }, []);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="relative aspect-[2/3] w-full overflow-hidden"
    >
      {/* Poster Image */}
      {inView && (
        <img
          src={posterPath}
          alt={title}
          loading="lazy"
          onLoad={handleImageLoad}
          className={`size-full object-cover transition-transform duration-300 will-change-transform group-hover:scale-105 ${
            isImageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
      {!isImageLoaded && (
        <div className="flex size-full items-center justify-center bg-gray-700">
          <span className="text-4xl text-gray-400">🎬</span>
        </div>
      )}

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
