// import React from 'react';
import { useNavigate } from 'react-router-dom';

const ErrorPage = ({ code = 404, message = 'Page Not Found' }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-background flex min-h-screen flex-col items-center justify-center px-4 transition-colors duration-200">
      {/* Animated Illustration */}
      <div className="relative mb-8 flex items-center justify-center">
        <div className="absolute size-40 animate-ping rounded-full bg-red-600 opacity-30" />
        <svg
          className="animate-float z-10 size-40"
          viewBox="0 0 200 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <ellipse cx="100" cy="100" rx="90" ry="60" fill="#1F2937" />
          <ellipse cx="100" cy="100" rx="70" ry="45" fill="#EF4444" opacity="0.15" />
          <g>
            <circle cx="100" cy="100" r="38" fill="#fff" />
            <rect x="80" y="90" width="40" height="20" rx="10" fill="#EF4444" />
            <circle cx="90" cy="100" r="4" fill="#fff" />
            <circle cx="110" cy="100" r="4" fill="#fff" />
            <ellipse cx="100" cy="110" rx="8" ry="4" fill="#1F2937" />
          </g>
        </svg>
      </div>
      {/* Error Code & Message */}
      <div className="text-center">
        <h1 className="animate-bounce-slow mb-4 text-7xl font-extrabold text-red-600">{code}</h1>
        <h2 className="animate-fade-in text-foreground mb-2 text-2xl font-bold">{message}</h2>
        <p className="animate-fade-in mb-8 text-gray-400">
          Sorry, the page you are looking for does not exist or an error occurred.
        </p>
        <button
          onClick={() => navigate('/')}
          className="animate-fade-in rounded bg-red-600 px-6 py-2 font-semibold text-white shadow-lg transition hover:bg-red-700"
        >
          Go Home
        </button>
      </div>
      {/* Custom Animations */}
      <style>{`
        @keyframes float {
          0% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
          100% { transform: translateY(0px); }
        }
        .animate-float { animation: float 3s ease-in-out infinite; }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        .animate-bounce-slow { animation: bounce-slow 2s infinite; }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-fade-in { animation: fade-in 1.2s ease-in; }
      `}</style>
    </div>
  );
};

export default ErrorPage;
