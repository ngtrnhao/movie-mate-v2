import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

const CastSection = ({ cast = [] }) => {
  const { t } = useTranslation('movies');

  if (!cast || cast.length === 0) return null;

  // Handle different data formats from backend
  const getDisplayCast = () => {
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
          {displayCast.map(actor => (
            <motion.div
              key={actor.cast_id || actor.id || `${actor.name}-${actor.order}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800"
            >
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img
                  src={getImageUrl(actor.profile_path)}
                  alt={actor.name}
                  className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={e => {
                    e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                  }}
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                <h3 className="text-sm font-semibold text-white">{actor.name}</h3>
                <p className="mt-1 text-xs text-gray-300">{getCharacterName(actor)}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Cast Button */}
        {cast.length > 6 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-8 flex justify-center"
          >
            <button className="rounded-lg border border-white/20 px-6 py-3 text-white hover:bg-white/10">
              View All Cast ({cast.length})
            </button>
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default CastSection;
