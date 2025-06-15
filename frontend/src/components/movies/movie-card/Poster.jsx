import { motion } from 'framer-motion';

const Poster = ({ posterPath, title }) => {
  // Use posterPath directly as it's already the full URL from our API
  const imageUrl = posterPath;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="relative aspect-[2/3] w-full overflow-hidden"
    >
      {/* Poster Image */}
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={title}
          className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
        />
      ) : (
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
};

export default Poster;
