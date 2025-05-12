import { useTranslation as useTranslationOriginal } from 'react-i18next';

export const useTranslation = (ns = 'common') => {
  const { t, i18n } = useTranslationOriginal(ns);

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  return {
    t,
    i18n,
    changeLanguage,
    currentLanguage: i18n.language,
  };
};
