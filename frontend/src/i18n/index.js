import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations
import enCommon from './locales/en/common.json';
import enLanding from './locales/en/landing.json';
import enMovies from './locales/en/movies.json';
import enReviews from './locales/en/reviews.json';
import enAuth from './locales/en/auth.json';

import viCommon from './locales/vi/common.json';
import viLanding from './locales/vi/landing.json';
import viMovies from './locales/vi/movies.json';
import viReviews from './locales/vi/reviews.json';
import viAuth from './locales/vi/auth.json';

const resources = {
  en: {
    common: enCommon,
    landing: enLanding,
    movies: enMovies,
    reviews: enReviews,
    auth: enAuth,
  },
  vi: {
    common: viCommon,
    landing: viLanding,
    movies: viMovies,
    reviews: viReviews,
    auth: viAuth,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    ns: ['common', 'landing', 'movies', 'reviews', 'auth'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
