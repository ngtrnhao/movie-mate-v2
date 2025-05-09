import PlanCard from './PlanCard';

const plans = [
  {
    name: 'Basic',
    price: 0,
    period: 'month',
    description: 'Perfect for casual movie watchers',
    features: [
      'Access to movie database',
      'Limited recommendations',
      'Standard definition streaming',
      'Ad-supported experience',
    ],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Premium',
    price: 9.99,
    period: 'month',
    description: 'Ideal for movie enthusiasts',
    features: [
      'Full access to all movies',
      'Unlimited personalized recommendations',
      'HD streaming quality',
      'Ad-free experience',
      'Download movies for offline viewing',
    ],
    cta: 'Get Started',
    highlighted: true,
    badge: 'Most Popular',
  },
  {
    name: 'Family',
    price: 14.99,
    period: 'month',
    description: 'Great for the whole family',
    features: [
      'Everything in Premium',
      'Up to 5 user profiles',
      'Parental controls',
      '4K Ultra HD streaming',
      'Simultaneous streaming on multiple devices',
    ],
    cta: 'Get Started',
    highlighted: false,
  },
];

const PlanList = () => {
  return (
    <div className="flex w-full flex-col items-center justify-center  gap-8 md:flex-row">
      {plans.map((plan, idx) => (
        <PlanCard key={idx} plan={plan} />
      ))}
    </div>
  );
};

export default PlanList;
