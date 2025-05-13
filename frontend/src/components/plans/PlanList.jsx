import PlanCard from './PlanCard';
import { useTranslation } from '../../i18n/hooks/useTranslation';

const PlanList = () => {
  const { t } = useTranslation('landing');
  const plans = [
    {
      ...t('plans.basic', { returnObjects: true }),
      price: 0,
      period: 'month',
      highlighted: false,
    },
    {
      ...t('plans.premium', { returnObjects: true }),
      price: 4.99,
      period: 'month',
      highlighted: true,
    },
    {
      ...t('plans.family', { returnObjects: true }),
      price: 7.99,
      period: 'month',
      highlighted: false,
    },
  ];

  return (
    <div className="flex w-full flex-col items-center justify-center  gap-8 md:flex-row">
      {plans.map((plan, idx) => (
        <PlanCard key={idx} plan={plan} />
      ))}
    </div>
  );
};

export default PlanList;
