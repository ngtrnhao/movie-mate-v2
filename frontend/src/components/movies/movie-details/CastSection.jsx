import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Users, UserX } from 'lucide-react';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

const CastSection = ({ cast = [], isLoading = false, error = null }) => {
  const { t } = useTranslation('movies');

  // Handle different data formats from backend
  const getDisplayCast = () => {
    if (!cast || !Array.isArray(cast)) return [];
    return cast.filter(member => member.role === 'ACTOR' || !member.role).slice(0, 6);
  };

  const getImageUrl = path => {
    if (!path) return 'https://via.placeholder.com/500x750?text=No+Image';
    if (path.startsWith('http')) return path;
    return `${TMDB_IMAGE_BASE_URL}${path}`;
  };

  const getCharacterName = member => {
    if (member.character) return member.character;
    if (member.main_character) return member.main_character;
    if (member.all_characters && member.all_characters.length > 0) {
      return member.all_characters[0];
    }
    return 'Actor';
  };

  const displayCast = getDisplayCast();
  const hasCast = displayCast && displayCast.length > 0;

  // Loading state
  if (isLoading) {
    return (
      <section className="relative mt-32 bg-gray-900 pb-16">
        <div className="container mx-auto px-4">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-8 text-2xl font-bold text-white sm:text-3xl"
          >
            {t('details.cast')}
          </motion.h2>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {[...Array(6)].map((_, index) => (
              <div
                key={index}
                className="group relative overflow-hidden rounded-lg bg-gray-800 animate-pulse"
              >
                <div className="aspect-[2/3] w-full bg-gray-700"></div>
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                  <div className="h-4 bg-gray-600 rounded mb-2"></div>
                  <div className="h-3 bg-gray-700 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section className="relative mt-32 bg-gray-900 pb-16">
        <div className="container mx-auto px-4">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-8 text-2xl font-bold text-white sm:text-3xl"
          >
            {t('details.cast')}
          </motion.h2>

          <div className="flex flex-col items-center justify-center py-12 text-center">
            <UserX className="w-16 h-16 text-gray-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">
              Không thể tải thông tin diễn viên
            </h3>
            <p className="text-gray-500 mb-4">
              Đã xảy ra lỗi khi tải danh sách diễn viên. Vui lòng thử lại sau.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Thử lại
            </button>
          </div>
        </div>
      </section>
    );
  }

  // Empty state
  if (!hasCast) {
    return (
      <section className="relative mt-32 bg-gray-900 pb-16">
        <div className="container mx-auto px-4">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-8 text-2xl font-bold text-white sm:text-3xl"
          >
            {t('details.cast')}
          </motion.h2>

          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Users className="w-16 h-16 text-gray-600 mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">
              Chưa có thông tin diễn viên
            </h3>
            <p className="text-gray-500">
              Thông tin về diễn viên cho bộ phim này sẽ được cập nhật sớm.
            </p>
          </div>
        </div>
      </section>
    );
  }

  // Normal state with cast data
  return (
    <section className="relative mt-32 bg-gray-900 pb-16">
      <div className="container mx-auto px-4">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-8 text-2xl font-bold text-white sm:text-3xl"
        >
          {t('details.cast')}
        </motion.h2>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {displayCast.map((actor, index) => (
            <motion.div
              key={actor.cast_id || actor.id || `${actor.name}-${actor.order}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800"
            >
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img
                  src={getImageUrl(actor.profile_path)}
                  alt={actor.name || 'Actor'}
                  className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={e => {
                    e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                  }}
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                <h3 className="text-sm font-semibold text-white line-clamp-1">
                  {actor.name || 'Unknown Actor'}
                </h3>
                <p className="mt-1 text-xs text-gray-300 line-clamp-1">{getCharacterName(actor)}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Cast Button */}
        {cast && cast.length > 6 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-8 flex justify-center"
          >
            <button className="rounded-lg border border-white/20 px-6 py-3 text-white hover:bg-white/10 transition-colors">
              Xem tất cả diễn viên ({cast.length})
            </button>
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default CastSection;
