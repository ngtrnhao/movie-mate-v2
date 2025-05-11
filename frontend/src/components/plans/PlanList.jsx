import PlanCard from './PlanCard';

const plans = [
  {
    name: 'Basic',
    price: 0,
    period: 'month',
    description: 'Perfect for casual movie fans',
    features: [
      'Explore a vast and diverse movie library',
      'Limited personalized recommendations',
      'Create a basic watchlist',
      'Read and write reviews',
    ],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Premium',
    price: 4.99,
    period: 'month',
    description: 'Ideal for movie enthusiasts',
    features: [
      'Unlimited personalized recommendations',
      'Advanced movie discovery filters',
      'Unlimited watchlists',
      'Priority access to new features',
      'Ad-free experience',
      'Community badges & stats',
    ],
    cta: 'Go Premium',
    highlighted: true,
    badge: 'Most Popular',
  },
  {
    name: 'Family',
    price: 7.99,
    period: 'month',
    description: 'Great for the whole family',
    features: [
      'Everything in Premium',
      'Up to 5 user profiles',
      'Parental controls for watchlists',
      'Share recommendations with family',
      'Collaborative family watchlist',
    ],
    cta: 'Start Family Plan',
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
