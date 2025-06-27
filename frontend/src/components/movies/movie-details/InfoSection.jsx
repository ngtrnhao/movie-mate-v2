// import { motion } from 'framer-motion';
// import { Play, Bookmark } from 'lucide-react';
// import { useTranslation } from '../../../i18n/hooks/useTranslation';

// const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/original';

// const InfoSection = ({ movie }) => {
//   const { t } = useTranslation('movies');

//   if (!movie) return null;

//   // Handle different image URL formats
//   const getImageUrl = path => {
//     if (!path) return null;
//     if (path.startsWith('http')) return path;
//     return `${TMDB_IMAGE_BASE_URL}${path}`;
//   };

//   // Get the best available overview
//   const getOverview = () => {
//     if (movie.overviews?.vi) return movie.overviews.vi;
//     if (movie.overviews?.en) return movie.overviews.en;
//     if (movie.overview_vi) return movie.overview_vi;
//     if (movie.overview_en) return movie.overview_en;
//     if (movie.overview) return movie.overview;
//     return '';
//   };

//   // Get the best available title
//   const getTitle = () => {
//     if (movie.title_vi) return movie.title_vi;
//     if (movie.title_en) return movie.title_en;
//     if (movie.title) return movie.title;
//     if (movie.original_title) return movie.original_title;
//     return 'No Title';
//   };

//   // Get rating info
//   const getRating = () => {
//     if (movie.cached_imdb_rating) return parseFloat(movie.cached_imdb_rating);
//     if (movie.imdb_rating) return parseFloat(movie.imdb_rating);
//     if (movie.cached_tmdb_rating) return parseFloat(movie.cached_tmdb_rating);
//     if (movie.tmdb_rating) return parseFloat(movie.tmdb_rating);
//     if (movie.vote_average) return parseFloat(movie.vote_average);
//     return 0;
//   };

//   // Get genre names
//   const getGenres = () => {
//     if (movie.genres) return movie.genres;
//     return [];
//   };

//   // Get trailer URL
//   const getTrailerUrl = () => {
//     if (movie.trailerUrl) return movie.trailerUrl;
//     if (movie.trailers && movie.trailers.length > 0) {
//       const trailer = movie.trailers.find(t => t.type === 'TRAILER') || movie.trailers[0];
//       return `https://www.youtube.com/watch?v=${trailer.youtube_key}`;
//     }
//     return null;
//   };

//   return (
//     <div className="relative h-[90vh] w-full overflow-hidden">
//       {/* Backdrop */}
//       <div
//         className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
//         style={{
//           backgroundImage: `url(${getImageUrl(movie.backdrop_url || movie.backdrop_path || movie.poster_url)})`,
//           backgroundSize: 'cover', // Đảm bảo phủ kín
//           backgroundPosition: 'center center',
//           backgroundRepeat: 'no-repeat',
//         }}
//       />
//       {/* Gradient phủ hai bên */}
//       <div
//         className="pointer-events-none absolute inset-0 z-20"
//         style={{
//           background:
//             'linear-gradient(90deg, #18181b 0%, rgba(24,24,27,0.0) 20%, rgba(24,24,27,0.0) 80%, #18181b 100%)',
//         }}
//       ></div>
//       {/* Overlay làm tối */}
//       <div className="absolute inset-0 bg-black/20 z-10"></div>
//       {/* Dot Grid Overlay */}
//       <div className="bg-dot-grid absolute inset-0 z-20"></div>

//       {/* Content */}
//       <div className="absolute inset-x-0 bottom-20 pr-36 z-30">
//         <div className="container mx-auto">
//           <div className="flex gap-8">
//             {/* Poster */}
//             <motion.img
//               initial={{ opacity: 0, y: 20 }}
//               animate={{ opacity: 1, y: 0 }}
//               src={getImageUrl(movie.poster_url || movie.poster_path)}
//               alt={getTitle()}
//               className="h-[400px] w-[266px] rounded-lg shadow-2xl"
//               onError={e => {
//                 e.target.src = 'https://via.placeholder.com/266x400?text=No+Image';
//               }}
//             />

//             {/* Info */}
//             <div className="flex-1 text-white">
//               <h1 className="text-4xl font-bold">{getTitle()}</h1>
//               <div className="mt-2 flex items-center gap-4">
//                 {movie.release_date && (
//                   <>
//                     <span>{new Date(movie.release_date).getFullYear()}</span>
//                     <span>•</span>
//                   </>
//                 )}
//                 {movie.runtime && (
//                   <>
//                     <span>{movie.runtime} min</span>
//                     <span>•</span>
//                   </>
//                 )}
//                 <div className="flex items-center">
//                   <span className="text-yellow-400">★</span>
//                   <span className="ml-1">{getRating().toFixed(1)}</span>
//                 </div>
//               </div>

//               {/* Genres */}
//               {getGenres().length > 0 && (
//                 <div className="mt-4 flex gap-2">
//                   {getGenres().map(genre => (
//                     <span
//                       key={genre.id || genre.name}
//                       className="rounded-full bg-red-700/20 px-3 py-1 text-sm text-red-400"
//                     >
//                       {genre.name}
//                     </span>
//                   ))}
//                 </div>
//               )}

//               {/* Overview */}
//               {getOverview() && <p className="mt-6 text-lg text-gray-300">{getOverview()}</p>}

//               {/* Actions */}
//               <div className="mt-8 flex gap-4">
//                 {getTrailerUrl() && (
//                   <button
//                     onClick={() => window.open(getTrailerUrl(), '_blank')}
//                     className="flex items-center gap-2 rounded-md bg-red-600 px-6 py-3 text-white hover:bg-red-700"
//                   >
//                     <Play className="size-5" />
//                     Watch Trailer
//                   </button>
//                 )}
//                 <button className="flex items-center gap-2 rounded-md border border-white/20 px-6 py-3 text-white hover:bg-white/10">
//                   <Bookmark className="size-5" />
//                   Add to Watchlist
//                 </button>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//       {/* Movie Info Overlay */}
//     </div>
//   );
// };

// export default InfoSection;
