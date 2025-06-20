import PlanCard from './PlanCard';
import { useTranslation } from '../../i18n/hooks/useTranslation';

const PlanList = ({ icons, onSelectPlan }) => {
  const { t } = useTranslation('landing');
  const plans = [
    {
      ...t('plans.basic', { returnObjects: true }),
      highlighted: false,
      id: 'prenium_basic',
    },
    {
      ...t('plans.standard', { returnObjects: true }),
      highlighted: true,
      id: 'prenium_standard',
    },
    {
      ...t('plans.vip', { returnObjects: true }),
      highlighted: false,
      id: 'prenium_vip',
    },
  ];

  return (
    <div className="flex w-full flex-col items-center justify-center gap-8 md:flex-row">
      {plans.map((plan, idx) => (
        <PlanCard
          key={idx}
          plan={plan}
          icon={icons ? icons[idx] : undefined}
          onSelect={() => onSelectPlan && onSelectPlan(plan)}
        />
      ))}
    </div>
  );
};

export default PlanList;
