import { NavLink } from 'react-router-dom';
import { useTranslation } from '../../i18n/hooks/useTranslation';
const Navigation = () => {
  const { t } = useTranslation('common');
  return (
    <nav className="hidden items-center gap-8 md:flex">
      <NavLink
        to="/"
        className={({ isActive }) =>
          isActive ? 'text-primary' : 'text-muted-foreground hover:text-primary transition-colors'
        }
      >
        {t('nav.home')}
      </NavLink>
      <NavLink
        to="/watchlist"
        className={({ isActive }) =>
          isActive ? 'text-primary' : 'text-muted-foreground hover:text-primary transition-colors'
        }
      >
        {t('nav.watchlist')}
      </NavLink>
    </nav>
  );
};

export default Navigation;
