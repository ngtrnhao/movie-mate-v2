import { MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

function ThumbsUp(props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M7 10v12" />
      <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z" />
    </svg>
  );
}

// function MessageSquare(props) {
//   return (
//     <svg
//       xmlns="http://www.w3.org/2000/svg"
//       width="16"
//       height="16"
//       viewBox="0 0 24 24"
//       fill="none"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//       {...props}
//     >
//       <rect x="3" y="3" width="18" height="18" rx="2" />
//       <path d="M8 10h.01" />
//       <path d="M12 10h.01" />
//       <path d="M16 10h.01" />
//     </svg>
//   );
// }

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: 'easeOut',
    },
  },
  hover: {
    scale: 1.02,
    transition: {
      duration: 0.2,
      ease: 'easeInOut',
    },
  },
};

const iconVariants = {
  hover: {
    scale: 1.1,
    transition: {
      duration: 0.2,
    },
  },
};

const ReviewCard = ({ review }) => (
  <motion.div
    variants={cardVariants}
    initial="hidden"
    animate="visible"
    whileHover="hover"
    className="flex min-h-[180px] rounded-xl border border-gray-700 bg-gray-800 p-4 shadow"
  >
    <motion.div
      className="flex h-32 w-24 shrink-0 items-center justify-center rounded-lg bg-gray-700"
      whileHover={{ backgroundColor: '#4B5563' }}
      transition={{ duration: 0.2 }}
    >
      <motion.span className="text-2xl text-gray-400" variants={iconVariants}>
        🎬
      </motion.span>
    </motion.div>
    <div className="ml-4 flex flex-1 flex-col">
      <div className="flex flex-col items-start gap-2">
        <motion.span
          className="line-clamp-1 text-base font-bold text-white"
          whileHover={{ color: '#F3F4F6' }}
          transition={{ duration: 0.2 }}
        >
          {review.movieTitle}
        </motion.span>
        <motion.span className="text-sm text-yellow-400" variants={iconVariants}>
          {'★'.repeat(review.rating)}
          {'☆'.repeat(5 - review.rating)}
        </motion.span>
      </div>
      <div className="my-1 flex items-center gap-2 text-sm text-gray-400">
        <motion.img
          src={review.userAvatar}
          className="size-6 rounded-full bg-gray-600"
          alt="avatar"
          variants={iconVariants}
        />
        <motion.span
          className="font-semibold text-gray-200"
          whileHover={{ color: '#F3F4F6' }}
          transition={{ duration: 0.2 }}
        >
          {review.userName}
        </motion.span>
        <motion.span whileHover={{ opacity: 0.8 }} transition={{ duration: 0.2 }}>
          {review.date}
        </motion.span>
      </div>
      <motion.p
        className="mb-2 line-clamp-2 text-sm text-gray-300"
        whileHover={{ color: '#E5E7EB' }}
        transition={{ duration: 0.2 }}
      >
        {review.text}
      </motion.p>
      <div className="mt-auto flex items-center gap-4 text-xs text-gray-400">
        <motion.span
          className="flex items-center gap-1"
          whileHover={{ color: '#D1D5DB' }}
          transition={{ duration: 0.2 }}
        >
          <motion.div variants={iconVariants}>
            <ThumbsUp className="size-4" />
          </motion.div>
          {review.likes}
        </motion.span>
        <motion.span
          className="flex items-center gap-1"
          whileHover={{ color: '#D1D5DB' }}
          transition={{ duration: 0.2 }}
        >
          <motion.div variants={iconVariants}>
            <MessageSquare className="size-4" />
          </motion.div>
          {review.comments}
        </motion.span>
        <motion.button
          className="ml-auto text-gray-400"
          whileHover={{
            color: '#EF4444',
            textDecoration: 'underline',
          }}
          transition={{ duration: 0.2 }}
        >
          Read More
        </motion.button>
      </div>
    </div>
  </motion.div>
);

export default ReviewCard;
