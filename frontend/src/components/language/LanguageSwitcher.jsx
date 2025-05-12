import { useTranslation } from '../../i18n/hooks/useTranslation';

const LanguageSwitcher = () => {
  const { currentLanguage, changeLanguage } = useTranslation();

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={() => changeLanguage('en')}
        className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
          currentLanguage === 'en'
            ? 'bg-red-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => changeLanguage('vi')}
        className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
          currentLanguage === 'vi'
            ? 'bg-red-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
        }`}
      >
        VI
      </button>
    </div>
  );
};

export default LanguageSwitcher;
