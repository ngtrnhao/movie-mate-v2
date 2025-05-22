const ErrorMessage = ({ title, message }) => (
  <div className="text-center text-red-500">
    <h2 className="mb-2 text-2xl font-bold">{title}</h2>
    <p>{message}</p>
  </div>
);

export default ErrorMessage;
