const EmptyState = ({ title, message }) => (
  <div className="text-center text-gray-400">
    <h2 className="mb-2 text-2xl font-bold">{title}</h2>
    <p className="text-lg">{message}</p>
  </div>
);

export default EmptyState;
