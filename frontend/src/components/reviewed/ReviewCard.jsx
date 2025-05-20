import { MessageSquare } from 'lucide-react';
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

const ReviewCard = ({ review }) => (
  <div className="flex min-h-[180px] rounded-xl border border-gray-700 bg-gray-800 p-4 shadow transition hover:shadow-lg">
    <div className="flex h-32 w-24 shrink-0 items-center justify-center rounded-lg bg-gray-700">
      {/* Poster image or placeholder */}
      <span className="text-2xl text-gray-400">🎬</span>
    </div>
    <div className="ml-4 flex flex-1 flex-col">
      <div className="flex flex-col items-start gap-2">
        <span className="line-clamp-1  text-base font-bold text-white">{review.movieTitle}</span>
        {/* Rating stars */}
        <span className="text-sm text-yellow-400">
          {'★'.repeat(review.rating)}
          {'☆'.repeat(5 - review.rating)}
        </span>
      </div>
      <div className="my-1 flex items-center gap-2 text-sm text-gray-400">
        <img src={review.userAvatar} className="size-6 rounded-full bg-gray-600" alt="avatar" />
        <span className="font-semibold text-gray-200">{review.userName}</span>
        <span>{review.date}</span>
      </div>
      <p className="mb-2 line-clamp-2 text-sm text-gray-300">{review.text}</p>
      <div className="mt-auto flex items-center gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <ThumbsUp className="size-4" />
          {review.likes}
        </span>
        <span className="flex items-center gap-1">
          <MessageSquare className="size-4" />
          {review.comments}
        </span>
        <button className="ml-auto text-blue-400 hover:underline">Read More</button>
      </div>
    </div>
  </div>
);

export default ReviewCard;
