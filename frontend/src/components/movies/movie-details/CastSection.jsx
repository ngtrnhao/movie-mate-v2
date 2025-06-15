import { motion } from 'framer-motion';
import { useTranslation } from '../../../i18n/hooks/useTranslation';

const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

// Mock data cho cast
const mockCast = [
  {
    adult: false,
    gender: 2,
    id: 1,
    known_for_department: 'Acting',
    name: 'Christian Bale',
    original_name: 'Christian Bale',
    popularity: 20.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 1,
    character: 'Bruce Wayne / Batman',
    credit_id: '52fe4281c3a36847f8024f49',
    order: 0,
  },
  {
    adult: false,
    gender: 2,
    id: 2,
    known_for_department: 'Acting',
    name: 'Heath Ledger',
    original_name: 'Heath Ledger',
    popularity: 18.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 2,
    character: 'Joker',
    credit_id: '52fe4281c3a36847f8024f4d',
    order: 1,
  },
  {
    adult: false,
    gender: 1,
    id: 3,
    known_for_department: 'Acting',
    name: 'Anne Hathaway',
    original_name: 'Anne Hathaway',
    popularity: 15.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 3,
    character: 'Selina Kyle / Catwoman',
    credit_id: '52fe4281c3a36847f8024f51',
    order: 2,
  },
  {
    adult: false,
    gender: 2,
    id: 4,
    known_for_department: 'Acting',
    name: 'Gary Oldman',
    original_name: 'Gary Oldman',
    popularity: 12.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 4,
    character: 'Commissioner Gordon',
    credit_id: '52fe4281c3a36847f8024f55',
    order: 3,
  },
  {
    adult: false,
    gender: 2,
    id: 5,
    known_for_department: 'Acting',
    name: 'Tom Hardy',
    original_name: 'Tom Hardy',
    popularity: 14.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 5,
    character: 'Bane',
    credit_id: '52fe4281c3a36847f8024f59',
    order: 4,
  },
  {
    adult: false,
    gender: 1,
    id: 6,
    known_for_department: 'Acting',
    name: 'Marion Cotillard',
    original_name: 'Marion Cotillard',
    popularity: 10.0,
    profile_path: '/2v9FVVBUrrkW2m3QOcYkuhq9A6o.jpg',
    cast_id: 6,
    character: 'Miranda Tate',
    credit_id: '52fe4281c3a36847f8024f5d',
    order: 5,
  },
];

const CastSection = ({ cast }) => {
  const { t } = useTranslation('movies');

  // Sử dụng mock data nếu không có cast data
  const displayCast = cast || mockCast;

  if (!displayCast || displayCast.length === 0) return null;

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
          {displayCast.slice(0, 6).map(actor => (
            <motion.div
              key={actor.cast_id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.05 }}
              className="group relative overflow-hidden rounded-lg bg-gray-800/50 transition-all duration-300 hover:bg-gray-800/70"
            >
              {/* Actor Image */}
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img
                  src={`${TMDB_IMAGE_BASE_URL}${actor.profile_path}`}
                  alt={actor.name}
                  className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={e => {
                    e.target.onerror = null;
                    e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                  }}
                />
              </div>

              {/* Actor Info */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                <h3 className="text-sm font-semibold text-white">{actor.name}</h3>
                <p className="mt-1 text-xs text-gray-300">{actor.character}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View All Cast Button */}
        {displayCast.length > 6 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-8 flex justify-center"
          >
            <button className="rounded-md border border-white/20 px-6 py-2 text-sm text-white transition-colors hover:bg-white/10">
              {t('details.viewAllCast')}
            </button>
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default CastSection;
