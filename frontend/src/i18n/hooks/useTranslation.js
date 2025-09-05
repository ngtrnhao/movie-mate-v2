import { useTranslation as useTranslationOriginal } from 'react-i18next';
import { useEffect } from 'react';

const LANGUAGE_KEY = 'app_language';
const DEFAULT_LANGUAGE = 'en';

export const useTranslation = (ns = 'common') => {
  const { t, i18n } = useTranslationOriginal(ns);

  const changeLanguage = lng => {
    try {
      localStorage.setItem(LANGUAGE_KEY, lng);
      i18n.changeLanguage(lng);
    } catch (error) {
      console.error('Error saving language to localStorage:', error);
    }
  };

  useEffect(() => {
    try {
      const savedLanguage = localStorage.getItem(LANGUAGE_KEY);
      if (savedLanguage && savedLanguage !== i18n.language) {
        i18n.changeLanguage(savedLanguage);
      }
    } catch (error) {
      console.error('Error reading language from localStorage:', error);
    }
  }, [i18n]);

  const getStoredLanguage = () => {
    try {
      return localStorage.getItem(LANGUAGE_KEY) || DEFAULT_LANGUAGE;
    } catch (error) {
      return DEFAULT_LANGUAGE;
    }
  };

  return {
    t,
    i18n,
    changeLanguage,
    currentLanguage: i18n.language || DEFAULT_LANGUAGE,
    app_language: getStoredLanguage(),
  };
};
