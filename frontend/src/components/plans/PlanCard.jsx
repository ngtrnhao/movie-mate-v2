import { CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const PlanCard = ({ plan, icon, onSelect }) => (
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
        className="absolute -top-6 left-1/2 -translate-x-1/2 rounded-full border-2 border-white bg-gradient-to-r from-red-500 via-yellow-400 to-red-500 px-6 py-2 text-base font-bold text-white shadow-xl"
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
      className={`mt-auto w-full rounded-xl py-3 text-lg font-semibold shadow-lg transition-colors duration-300 ${
        plan.highlighted
          ? 'bg-white text-red-600 hover:bg-gray-100'
          : 'bg-gray-700 text-white hover:bg-red-600'
      }`}
      onClick={onSelect}
    >
      {plan.cta}
    </motion.button>
  </motion.div>
);

export default PlanCard;
