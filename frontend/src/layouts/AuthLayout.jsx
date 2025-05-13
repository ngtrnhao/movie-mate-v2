import { Outlet } from 'react-router-dom';
import LanguageSwitcher from '../components/language/LanguageSwitcher';
import '../styles/auth.css';

const benefits = [
  {
    icon: '🎬',
    text: 'Save your favorite movies',
  },
  {
    icon: '⭐',
    text: 'Get personalized recommendations',
  },
  {
    icon: '💬',
    text: 'Rate and review films',
  },
];

const AuthLayout = () => (
  <div className="relative flex min-h-screen flex-col justify-between overflow-hidden bg-gradient-to-b from-gray-900 via-gray-900 to-black">
    {/* Animated radial gradient background */}
    <div className="pointer-events-none absolute inset-0 z-0">
      <div className="absolute left-1/2 top-1/4 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-red-600/10 blur-3xl" />
    </div>
    <header className="relative z-10 flex items-center justify-center py-8">
      <a href="/" className="flex items-center gap-2">
        <svg
          viewBox="0 0 24 24"
          className="size-8 text-red-600"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
          <path d="M7 2v20" />
          <path d="M17 2v20" />
          <path d="M2 12h20" />
          <path d="M2 7h5" />
          <path d="M2 17h5" />
          <path d="M17 17h5" />
          <path d="M17 7h5" />
        </svg>
        <span className="text-xl font-bold text-red-600">MovieMate</span>
      </a>
      <div className="absolute right-8 top-8">
        <LanguageSwitcher />
      </div>
    </header>
    {/* Slogan under logo */}
    <div className="z-10 mb-4 text-center text-base font-medium text-gray-400">
      Your personal cinema companion
    </div>
    <main className="z-10 flex w-full flex-1 items-center justify-center">
      <div className="flex w-full max-w-4xl flex-col-reverse items-center justify-center gap-12 px-4 lg:flex-row">
        {/* Benefits section (desktop only) */}
        <div className="hidden w-1/2 flex-col items-start justify-center pl-8 lg:flex">
          {/* Inline SVG illustration */}
          <svg
            viewBox="0 0 120 96"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="mb-8 w-72 max-w-full opacity-90 drop-shadow-xl"
          >
            <rect x="10" y="20" width="100" height="56" rx="8" fill="#232326" />
            <rect x="18" y="28" width="84" height="40" rx="4" fill="#fff" />
            <rect x="30" y="72" width="12" height="12" rx="3" fill="#ef4444" />
            <rect x="50" y="72" width="12" height="12" rx="3" fill="#ef4444" />
            <rect x="70" y="72" width="12" height="12" rx="3" fill="#ef4444" />
            <rect x="90" y="72" width="12" height="12" rx="3" fill="#ef4444" />
            <rect x="38" y="36" width="44" height="8" rx="2" fill="#e5e7eb" />
            <rect x="38" y="48" width="44" height="4" rx="2" fill="#e5e7eb" />
            <rect x="38" y="54" width="44" height="4" rx="2" fill="#e5e7eb" />
            <ellipse cx="60" cy="16" rx="28" ry="6" fill="#ef4444" fillOpacity="0.15" />
          </svg>
          <ul className="space-y-4">
            {benefits.map((b, i) => (
              <li key={i} className="flex items-center gap-3 text-lg text-gray-300">
                <span className="text-2xl">{b.icon}</span>
                <span>{b.text}</span>
              </li>
            ))}
          </ul>
        </div>
        {/* Auth form (Login, Register, etc.) */}
        <div className="w-full max-w-sm lg:w-1/2">
          <Outlet />
        </div>
      </div>
    </main>
    <footer className="z-10 border-t border-gray-800 py-6 text-center text-sm text-gray-400">
      © 2025 MovieMate. All rights reserved.
    </footer>
  </div>
);

export default AuthLayout;
