import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations
import enCommon from './locales/en/common.json';
import enLanding from './locales/en/landing.json';
import enMovies from './locales/en/movies.json';
import enReviews from './locales/en/reviews.json';
import enAuth from './locales/en/auth.json';
import enCheckout from './locales/en/checkout.json';
import enRating from './locales/en/rating.json';
import enProfile from './locales/en/profile.json';

import viCommon from './locales/vi/common.json';
import viLanding from './locales/vi/landing.json';
import viMovies from './locales/vi/movies.json';
import viReviews from './locales/vi/reviews.json';
import viAuth from './locales/vi/auth.json';
import viCheckout from './locales/vi/checkout.json';
import viRating from './locales/vi/rating.json';
import viProfile from './locales/vi/profile.json';

const resources = {
  en: {
    common: enCommon,
    landing: enLanding,
    movies: enMovies,
    reviews: enReviews,
    auth: enAuth,
    checkout: enCheckout,
    rating: enRating,
    profile: enProfile,
  },
  vi: {
    common: viCommon,
    landing: viLanding,
    movies: viMovies,
    reviews: viReviews,
    auth: viAuth,
    checkout: viCheckout,
    rating: viRating,
    profile: viProfile,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    ns: ['common', 'landing', 'movies', 'reviews', 'auth', 'checkout', 'rating', 'profile'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage'],
      lookupLocalStorage: 'app_language',
      caches: ['localStorage'],
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
