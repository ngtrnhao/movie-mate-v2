import { Check, X, Star, Settings } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTranslation } from '../../i18n/hooks/useTranslation';

const comparisonData = [
  {
    key: 'general',
    icon: Settings,
    features: [
      'advancedDiscovery',
      'saveFavorites',
      'createLists',
      'tagNotes',
      'rateReview',
      'editReview',
      'voteBadge',
      'analytics',
      'compareTaste',
      'exportData',
      'themesProfile',
      'community',
      'calendarSync',
      'adFree',
      'prioritySupport',
      'earlyAccess',
      'giftPremium',
      'partnerOffers',
    ],
  },
  {
    key: 'recommendation',
    icon: Star,
    features: [
      'demographicFiltering',
      'collaborativeFiltering',
      'emrs',
      'moodBased',
      'matchFriends',
      'discoverDaily',
      'explainableRec',
      'algoTuning',
      'tasteBehavior',
    ],
  },
];

const columns = ['guest', 'member', 'basic', 'standard', 'vip'];

const valueData = {
  advancedDiscovery: { guest: true, member: true, basic: true, standard: true, vip: true },
  saveFavorites: {
    guest: 'no',
    member: { type: 'movies', count: 50 },
    basic: { type: 'movies', count: 200 },
    standard: { type: 'movies', count: 1000 },
    vip: 'unlimited',
  },
  createLists: {
    guest: 'no',
    member: { type: 'lists', count: 1 },
    basic: { type: 'lists', count: 5 },
    standard: { type: 'lists', count: 20 },
    vip: 'unlimited',
  },
  tagNotes: { guest: false, member: false, basic: true, standard: true, vip: true },
  rateReview: {
    guest: 'no',
    member: { type: 'perDay', count: 10 },
    basic: { type: 'perDay', count: 50 },
    standard: { type: 'perDay', count: 100 },
    vip: 'unlimited',
  },
  editReview: { guest: false, member: false, basic: true, standard: true, vip: true },
  voteBadge: { guest: false, member: false, basic: true, standard: true, vip: true },
  analytics: { guest: false, member: false, basic: true, standard: true, vip: true },
  compareTaste: { guest: false, member: false, basic: false, standard: true, vip: true },
  exportData: { guest: false, member: false, basic: false, standard: true, vip: true },
  themesProfile: { guest: false, member: false, basic: true, standard: true, vip: true },
  community: { guest: false, member: false, basic: false, standard: true, vip: true },
  calendarSync: { guest: false, member: false, basic: false, standard: true, vip: true },
  adFree: { guest: false, member: false, basic: true, standard: true, vip: true },
  prioritySupport: { guest: false, member: false, basic: false, standard: true, vip: true },
  earlyAccess: { guest: false, member: false, basic: false, standard: false, vip: true },
  giftPremium: { guest: false, member: false, basic: false, standard: false, vip: true },
  partnerOffers: { guest: false, member: false, basic: false, standard: true, vip: true },
  demographicFiltering: { guest: true, member: true, basic: true, standard: true, vip: true },
  collaborativeFiltering: {
    guest: false,
    member: true,
    basic: 'advanced',
    standard: 'advanced',
    vip: 'advanced',
  },
  emrs: { guest: false, member: false, basic: false, standard: true, vip: true },
  moodBased: {
    guest: 'no',
    member: { type: 'moods', count: 3 },
    basic: { type: 'moods', count: 10 },
    standard: { type: 'moods', count: 20 },
    vip: 'unlimited',
  },
  matchFriends: { guest: false, member: false, basic: true, standard: true, vip: true },
  discoverDaily: { guest: false, member: false, basic: false, standard: true, vip: true },
  explainableRec: { guest: false, member: false, basic: true, standard: true, vip: true },
  algoTuning: { guest: false, member: false, basic: false, standard: false, vip: true },
  tasteBehavior: { guest: false, member: false, basic: true, standard: true, vip: true },
};

const PlanCell = ({ value, t }) => {
  if (typeof value === 'boolean') {
    return value ? (
      <Check className="mx-auto h-6 w-6 text-green-400" />
    ) : (
      <X className="mx-auto h-6 w-6 text-red-500" />
    );
  }
  if (typeof value === 'string') {
    if (value === 'unlimited')
      return (
        <span className="font-semibold text-green-400">
          {t('pricing.comparison.values.unlimited')}
        </span>
      );
    if (value === 'advanced')
      return (
        <span className="font-semibold text-yellow-400">
          {t('pricing.comparison.values.advanced')}
        </span>
      );
    if (value === 'no')
      return <span className="text-red-500">{t('pricing.comparison.values.no')}</span>;
    if (value === 'yes')
      return <span className="text-green-400">{t('pricing.comparison.values.yes')}</span>;
    return <span>{value}</span>;
  }
  if (typeof value === 'object' && value !== null) {
    if (value.type === 'moods') return t('pricing.comparison.values.moods', { count: value.count });
    if (value.type === 'movies')
      return t('pricing.comparison.values.movies', { count: value.count });
    if (value.type === 'lists') return t('pricing.comparison.values.lists', { count: value.count });
    if (value.type === 'perDay')
      return t('pricing.comparison.values.perDay', { count: value.count });
  }
  return <span>{value}</span>;
};

const FeatureComparisonTable = () => {
  const { t } = useTranslation('landing');

  return (
    <div className="overflow-x-auto rounded-2xl bg-gray-900/80 p-4 shadow-xl">
      <table className="min-w-full table-auto divide-y divide-gray-800">
        <thead className="sticky top-0 bg-gray-900/95">
          <tr>
            <th className="w-1/3 px-4 py-4 text-left text-base font-bold uppercase tracking-wider text-white">
              {t('pricing.comparison.featureCol', 'Feature')}
            </th>
            {columns.map(col => (
              <th
                key={col}
                className="w-1/6 px-4 py-4 text-center text-base font-bold uppercase tracking-wider text-white"
              >
                {t(`pricing.comparison.columns.${col}`)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {comparisonData.map((category, categoryIdx) => {
            const Icon = category.icon;
            return (
              <>
                <tr key={category.key}>
                  <td
                    colSpan={columns.length + 1}
                    className="bg-gray-800/90 px-6 py-4 rounded-t-2xl"
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="text-red-400" size={22} />
                      <span className="uppercase font-medium text-white flex items-center h-full">
                        {t(`pricing.comparison.categories.${category.key}.title`)}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {t(`pricing.comparison.categories.${category.key}.desc`)}
                    </div>
                  </td>
                </tr>
                {category.features.map((feature, featureIdx) => (
                  <motion.tr
                    key={feature}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: (categoryIdx * 5 + featureIdx) * 0.05 }}
                    className={
                      featureIdx % 2 === 0
                        ? 'bg-gray-900/80 hover:bg-gray-800/80'
                        : 'bg-gray-800/90 hover:bg-gray-700/80'
                    }
                  >
                    <td className="px-6 py-3 font-medium text-gray-200 text-left text-base">
                      {t(`pricing.comparison.features.${feature}`)}
                    </td>
                    {columns.map(col => (
                      <td key={col} className="px-4 py-3 text-center text-gray-300">
                        <PlanCell value={valueData[feature][col]} t={t} />
                      </td>
                    ))}
                  </motion.tr>
                ))}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default FeatureComparisonTable;
