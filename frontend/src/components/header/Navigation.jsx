import { NavLink } from 'react-router-dom';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useSelector } from 'react-redux';
import { selectHasAdminAccess, selectIsAdmin } from '../../store/slices/authSlice';

const Navigation = () => {
  const { t } = useTranslation('common');
  const hasAdminAccess = useSelector(selectHasAdminAccess);
  const isAdmin = useSelector(selectIsAdmin);
  return (
    <nav className="hidden items-center gap-8 md:flex">
      <NavLink
        to="/home"
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

      {/* Admin/Moderator Dashboard Links */}
      {hasAdminAccess && (
        <>
          {isAdmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                isActive ? 'text-red-200' : 'text-red-400 hover:text-red-300 transition-colors'
              }
            >
              Admin Dashboard
            </NavLink>
          )}
          <NavLink
            to="/moderator"
            className={({ isActive }) =>
              isActive ? 'text-blue-200' : 'text-blue-400 hover:text-blue-300 transition-colors'
            }
          >
            Moderator Dashboard
          </NavLink>
        </>
      )}
    </nav>
  );
};

export default Navigation;
