import { NavLink } from 'react-router-dom';
import { useTranslation } from '../../i18n/hooks/useTranslation';
const Navigation = () => {
  const { t } = useTranslation('common');
  return (
    <nav className="hidden items-center gap-8 md:flex">
      <NavLink
        to="/"
        className={({ isActive }) =>
          isActive ? 'text-yellow-200' : 'text-white hover:text-yellow-500 transition-colors'
        }
      >
        {t('nav.home')}
      </NavLink>
      <NavLink
        to="/movies"
        className={({ isActive }) =>
          isActive ? 'text-yellow-200' : 'text-white hover:text-yellow-500 transition-colors'
        }
      >
        {t('nav.movies')}
      </NavLink>
      <NavLink
        to="/pricing"
        className={({ isActive }) =>
          isActive ? 'text-yellow-200' : 'text-white hover:text-yellow-500 transition-colors'
        }
      >
        {t('nav.pricing', 'Pricing')}
      </NavLink>
      <NavLink
        to="/watchlist"
        className={({ isActive }) =>
          isActive ? 'text-yellow-200' : 'text-white hover:text-yellow-500 transition-colors'
        }
      >
        {t('nav.watchlist')}
      </NavLink>
    </nav>
  );
};

export default Navigation;
