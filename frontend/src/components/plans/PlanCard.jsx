import { CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSelector } from 'react-redux';
import { useQuery } from '@tanstack/react-query';
import { selectUser } from '../../store/slices/authSlice';
import { getPaymentTransactionAPI } from '../../api/profileService';

const PlanCard = ({ plan, icon, onSelect }) => {
  const user = useSelector(selectUser);

  const { data: currentSubscription, isLoading } = useQuery({
    queryKey: ['subscription', user?.id],
    queryFn: () => getPaymentTransactionAPI(user.id),
    enabled: !!user?.id,
  });

  // Helper functions
  const getPlanLevel = planName => {
    if (planName === 'basic') return 1;
    if (planName === 'standard') return 2;
    if (planName === 'vip') return 3;
    return 0;
  };

  const getCurrentPlanLevel = () => {
    if (!currentSubscription?.has_active_subscription) return 0;
    return getPlanLevel(currentSubscription.plan);
  };

  const getPlanName = () => {
    return plan.id.replace('premium_', '');
  };

  const isCurrentPlan = () => {
    if (!currentSubscription?.has_active_subscription) return false;
    return currentSubscription.plan === getPlanName();
  };

  const isUpgrade = () => {
    const currentLevel = getCurrentPlanLevel();
    const newLevel = getPlanLevel(getPlanName());
    return newLevel > currentLevel;
  };

  const isDowngrade = () => {
    const currentLevel = getCurrentPlanLevel();
    const newLevel = getPlanLevel(getPlanName());
    return newLevel < currentLevel;
  };

  const getButtonText = () => {
    if (isLoading) return 'Loading...';
    if (!user) return plan.cta;
    if (!currentSubscription?.has_active_subscription) return plan.cta;
    if (isCurrentPlan()) return 'Current Plan';
    if (isUpgrade()) return 'Upgrade';
    if (isDowngrade()) {
      if (!currentSubscription.can_downgrade) return 'Downgrade (30 days)';
      return 'Downgrade';
    }
    return plan.cta;
  };

  const getButtonStyle = () => {
    if (isLoading) return 'bg-gray-600 text-gray-400 cursor-not-allowed';
    if (!user)
      return plan.highlighted
        ? 'bg-white text-red-600 hover:bg-gray-100'
        : 'bg-gray-700 text-white hover:bg-red-600';
    if (!currentSubscription?.has_active_subscription)
      return plan.highlighted
        ? 'bg-white text-red-600 hover:bg-gray-100'
        : 'bg-gray-700 text-white hover:bg-red-600';
    if (isCurrentPlan()) return 'bg-red-600 text-white cursor-not-allowed';
    if (isUpgrade()) return 'bg-red-600 text-white hover:bg-red-700';
    if (isDowngrade()) {
      if (!currentSubscription.can_downgrade) return 'bg-gray-600 text-gray-400 cursor-not-allowed';
      return 'bg-yellow-600 text-white hover:bg-yellow-700';
    }
    return plan.highlighted
      ? 'bg-white text-red-600 hover:bg-gray-100'
      : 'bg-gray-700 text-white hover:bg-red-600';
  };

  const handleClick = () => {
    if (isLoading || isCurrentPlan()) return;
    if (isDowngrade() && !currentSubscription.can_downgrade) return;
    onSelect();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      whileHover={{ scale: 1.03 }}
      className={`group relative flex h-full min-w-[300px] flex-1 flex-col rounded-3xl bg-gray-800/60 p-8 text-white shadow-2xl transition-all duration-300 hover:bg-gray-800/80 ${
        plan.highlighted
          ? 'z-10 border-4 border-red-500 hover:shadow-red-500/30'
          : 'border border-gray-700 hover:border-gray-600'
      }`}
    >
      {/* Decorative Elements */}
      <div className="absolute -right-12 -top-12 size-24 rotate-12 bg-red-500/10 transition-transform duration-300 group-hover:scale-150" />

      {plan.badge && (
        <motion.span
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute -top-6 left-1/2 -translate-x-1/2 rounded-full border-2 border-white bg-gradient-to-r from-pink-600 via-red-400 to-red-500 px-6 py-2 text-base font-bold text-white shadow-xl"
          style={{ letterSpacing: 1 }}
        >
          {plan.badge}
        </motion.span>
      )}

      {/* Plan Icon */}
      {icon && <div className="mb-2 flex justify-center text-4xl drop-shadow-lg">{icon}</div>}

      {/* Plan Header */}
      <div className="relative mb-6">
        <h2 className="mb-2 text-2xl font-bold tracking-tight">{plan.name}</h2>
        <div className="flex items-baseline justify-center">
          <span className="text-4xl font-extrabold">${plan.price}</span>
          <span className="ml-2 text-base font-normal text-gray-400">/{plan.period}</span>
        </div>
        <p className="mt-2 text-center text-sm text-gray-400">{plan.description}</p>

        {/* Current subscription info */}
        {!isLoading && currentSubscription?.has_active_subscription && isCurrentPlan() && (
          <div className="mt-3 rounded-lg bg-green-900/30 p-2 text-center">
            <div className="text-xs font-semibold text-green-300">✓ Active Subscription</div>
            <div className="text-xs text-gray-300">
              Valid until {new Date(currentSubscription.subscription_end_date).toLocaleDateString()}
            </div>
          </div>
        )}

        {/* Upgrade indicator */}
        {!isLoading && currentSubscription?.has_active_subscription && isUpgrade() && (
          <div className="mt-3 rounded-lg bg-blue-900/30 p-2 text-center">
            <div className="text-xs font-semibold text-blue-300">⬆️ Upgrade Available</div>
            <div className="text-xs text-gray-300">Switch to higher tier</div>
          </div>
        )}

        {/* Downgrade indicator */}
        {!isLoading && currentSubscription?.has_active_subscription && isDowngrade() && (
          <div className="mt-3 rounded-lg bg-yellow-900/30 p-2 text-center">
            <div className="text-xs font-semibold text-yellow-300">⬇️ Downgrade Option</div>
            <div className="text-xs text-gray-300">
              {currentSubscription.can_downgrade
                ? 'Switch to lower tier'
                : `Available in ${currentSubscription.days_remaining - 30} days`}
            </div>
          </div>
        )}
      </div>

      {/* Features List */}
      <ul className="mb-8 grow space-y-3">
        {plan.features.map((feature, idx) => (
          <motion.li
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="flex items-center text-gray-300"
          >
            <CheckCircle
              className={`mr-3 size-5 ${plan.highlighted ? 'text-yellow-400' : 'text-red-500'}`}
            />
            <span className="text-sm">{feature}</span>
          </motion.li>
        ))}
      </ul>

      {/* CTA Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className={`mt-auto w-full rounded-xl py-3 text-lg font-semibold shadow-lg transition-colors duration-300 ${getButtonStyle()}`}
        onClick={handleClick}
      >
        {getButtonText()}
      </motion.button>
    </motion.div>
  );
};

export default PlanCard;
