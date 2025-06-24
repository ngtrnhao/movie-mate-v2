import FeatureComparisonTable from '../../components/plans/FeatureComparisonTable';
import PlanList from '../../components/plans/PlanList';
import SubscriptionStatus from '../../components/plans/SubscriptionStatus';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { selectUser } from '../../store/slices/authSlice';
// import { Film } from 'lucide-react';

const planIcons = [
  '🥉', // Basic
  '🥈', // Standard
  '🥇', // VIP
];

const PricingPage = () => {
  const { t } = useTranslation('landing');
  const navigate = useNavigate();
  const user = useSelector(selectUser);

  const handleSelectPlan = plan => {
    navigate(`/checkout?plan=${plan.id}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#3a1c71] via-[#d76d77] to-[#2e1a47] text-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="relative flex flex-col items-center justify-center pb-10 pt-16 text-center">
          {/* <span className="inline-flex items-center justify-center rounded-full bg-red-600/20 p-4 mb-4">
            <Film className="h-10 w-10 text-red-400" />
          </span> */}
          <h1 className="pt-20 text-4xl font-extrabold tracking-tight drop-shadow-lg sm:text-5xl">
            {t('pricing.title', 'Find the Perfect Plan')}
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-300">
            {t(
              'pricing.subtitle',
              'Unlock powerful features to supercharge your movie journey. Free 14-day trial on all plans.'
            )}
          </p>
        </div>

        {/* Current Subscription Status - Only show for logged in users */}
        {user && (
          <div className="mx-auto mt-8 max-w-2xl">
            <SubscriptionStatus />
          </div>
        )}

        {/* Plan Cards Section */}
        <div className="mt-12 flex flex-col items-center justify-center gap-10 lg:flex-row lg:items-stretch">
          <PlanList icons={planIcons} onSelectPlan={handleSelectPlan} />
        </div>
        {/* Section 2: Detailed Comparison Table */}
        <div className="mt-20 text-center sm:mt-24">
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            {t('pricing.compareTitle', 'Compare All Features')}
          </h2>
          <p className="mt-4 text-lg text-gray-400">
            {t('pricing.compareSubtitle', 'A detailed look at what each plan offers.')}
          </p>
          <p className="mt-2 text-base italic text-gray-400">
            {t('pricing.comparison.slogan', 'See what you get with each plan!')}
          </p>
        </div>
        <div className="mt-12">
          <FeatureComparisonTable />
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
