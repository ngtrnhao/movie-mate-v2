import { useState } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Users, UserX } from 'lucide-react';
import { getProfileUrl } from '../../../utils/imageUtils';

const CastSection = ({ cast = [], isLoading = false, error = null }) => {
  const { t } = useTranslation('movies');
  const [showAllCast, setShowAllCast] = useState(false);

  // Handle different data formats from backend
  const getDisplayCast = () => {
    if (!cast || !Array.isArray(cast)) return [];

    // Filter actors first
    const actors = cast.filter(member => member.role === 'ACTOR' || !member.role);

    // Prioritize actors with profile images, then fallback to actors without images
    const actorsWithImages = actors.filter(actor => actor.profile_path);
    const actorsWithoutImages = actors.filter(actor => !actor.profile_path);

    // Combine prioritized actors
    const prioritizedActors = [...actorsWithImages, ...actorsWithoutImages];

    // Return limited or all actors based on showAllCast state
    return showAllCast ? prioritizedActors : prioritizedActors.slice(0, 6);
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

  // DEBUG: Log cast data to console (remove this after testing)
  console.log(
    '🎭 Cast with images will show first:',
    displayCast.filter(actor => actor.profile_path).length + ' actors have profile images'
  );

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
                className="group relative animate-pulse overflow-hidden rounded-lg bg-gray-800"
              >
                <div className="aspect-[2/3] w-full bg-gray-700"></div>
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                  <div className="mb-2 h-4 rounded bg-gray-600"></div>
                  <div className="h-3 w-3/4 rounded bg-gray-700"></div>
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
            <UserX className="mb-4 size-16 text-gray-600" />
            <h3 className="mb-2 text-xl font-semibold text-gray-400">
              {t('details.cannotLoadCast')}
            </h3>
            <p className="mb-4 text-gray-500">{t('details.cannotLoadCastDesc')}</p>
            <button
              onClick={() => window.location.reload()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
            >
              {t('details.retry')}
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
            <Users className="mb-4 size-16 text-gray-600" />
            <h3 className="mb-2 text-xl font-semibold text-gray-400">{t('details.noCastInfo')}</h3>
            <p className="text-gray-500">{t('details.noCastInfoDesc')}</p>
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

        <div
          className={`grid gap-4 ${
            showAllCast
              ? 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6'
              : 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6'
          }`}
        >
          {displayCast.map((actor, index) => (
            <motion.div
              key={actor.cast_id || actor.id || `${actor.name}-${actor.order}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: showAllCast ? index * 0.05 : index * 0.1 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800"
            >
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img
                  src={getProfileUrl(actor, 'w500')}
                  alt={actor.name || 'Actor'}
                  className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={e => {
                    // Fallback to default avatar if both profile URL and gender-specific fallback fail
                    e.target.src = '/images/avatar_default.jpg';
                  }}
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                <h3 className="line-clamp-1 text-sm font-semibold text-white">
                  {actor.name || 'Unknown Actor'}
                </h3>
                <p className="mt-1 line-clamp-1 text-xs text-gray-300">{getCharacterName(actor)}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Cast Button */}
        {cast && cast.filter(member => member.role === 'ACTOR' || !member.role).length > 6 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-8 flex justify-center"
          >
            <button
              onClick={() => setShowAllCast(!showAllCast)}
              className="rounded-lg border border-white/20 px-6 py-3 text-white transition-colors hover:border-white/40 hover:bg-white/10"
            >
              {showAllCast
                ? t('details.collapseCast')
                : t('details.viewAllCast', {
                    count: cast.filter(member => member.role === 'ACTOR' || !member.role).length,
                  })}
            </button>
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default CastSection;
