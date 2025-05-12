import { useTranslation } from '../../i18n/hooks/useTranslation';

const LanguageSwitcher = () => {
  const { currentLanguage, changeLanguage } = useTranslation();

  const toggleLanguage = () => {
    changeLanguage(currentLanguage === 'en' ? 'vi' : 'en');
  };

  return (
    <button
      onClick={toggleLanguage}
      className="rounded-md border border-gray-600 px-4 py-2 text-white transition-colors hover:bg-white/10"
    >
      {currentLanguage === 'en' ? 'VI' : 'EN'}
    </button>
  );
};

export default LanguageSwitcher;
