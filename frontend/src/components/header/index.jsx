import SearchBar from './SearchBar';
import Navigation from './Navigation';
import MovieMateLogo from './Logo';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Menu, MenuItem, IconButton, Tooltip } from '@mui/material';
import { AccountCircle, Settings, Logout } from '@mui/icons-material';
import { logout } from '../../store/slices/authSlice';
import { selectIsAuthenticated, selectUser } from '../../store/selectors/authSelectors';
import UserBadge from '../common/UserBadge';
import { getUserType, USER_TYPES } from '../../utils/userPermissions';

const Header = () => {
  const { t } = useTranslation('common');
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isScrolled, setIsScrolled] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);
  const userType = getUserType(user);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleProfileMenuOpen = event => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleProfileClick = () => {
    handleProfileMenuClose();
    navigate(`/profile/${user.id}`);
  };

  const handleSettingsClick = () => {
    handleProfileMenuClose();
    navigate('/settings');
  };

  const handleLogout = () => {
    handleProfileMenuClose();
    dispatch(logout());
    window.location.href = '/login';
  };

  return (
    <header
      className={`fixed top-0 z-50 w-full transition-all duration-300 ${
        isScrolled ? 'bg-gray-900/90 backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <div className="mx-auto max-w-[1400px] px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
          <MovieMateLogo />

          {/* Center section */}
          <div className="flex flex-1 items-center justify-center">
            <div className="w-[400px]">
              <SearchBar />
            </div>
          </div>

          {/* Right section */}
          <div className="flex items-center space-x-4 md:space-x-6">
            <Navigation />
            <div className="flex items-center gap-2 md:gap-4">
              {isAuthenticated && user?.id ? (
                <>
                  <Tooltip
                    title={
                      <div className="text-center">
                        <div className="font-semibold">{user.username}</div>
                        {userType !== USER_TYPES.GUEST && (
                          <div className="text-xs opacity-75 mt-1">
                            {userType === USER_TYPES.MEMBER && 'Member'}
                            {userType === USER_TYPES.PREMIUM_BASIC && 'Premium Basic'}
                            {userType === USER_TYPES.PREMIUM_STANDARD && 'Premium Standard'}
                            {userType === USER_TYPES.PREMIUM_VIP && 'Premium VIP'}
                          </div>
                        )}
                      </div>
                    }
                    arrow
                    placement="bottom"
                  >
                    <IconButton
                      onClick={handleProfileMenuOpen}
                      size="large"
                      edge="end"
                      aria-label="account of current user"
                      aria-haspopup="true"
                      color="inherit"
                      sx={{ p: 0 }}
                    >
                      <div className="relative">
                        {/* Avatar Container with Enhanced Badge */}
                        <div className="group relative size-8 md:size-10 rounded-full bg-gradient-to-br from-red-500 to-red-700 p-0.5 shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl">
                          {/* User Badge - compact with text */}
                          {userType !== USER_TYPES.GUEST && (
                            <div className="absolute -top-2 -right-3 z-20">
                              <div className="relative">
                                {/* Premium glow for premium users only */}
                                {(userType === USER_TYPES.PREMIUM_BASIC ||
                                  userType === USER_TYPES.PREMIUM_STANDARD ||
                                  userType === USER_TYPES.PREMIUM_VIP) && (
                                  <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 opacity-60 blur-sm animate-pulse"></div>
                                )}

                                {/* Compact badge with text */}
                                <div
                                  className={`relative rounded-full border border-white/50 px-1.5 py-0.5 text-xs font-bold uppercase tracking-wider text-white shadow-lg transition-all duration-300 hover:scale-110 ${
                                    userType === USER_TYPES.MEMBER
                                      ? 'bg-blue-500'
                                      : userType === USER_TYPES.PREMIUM_BASIC
                                        ? 'bg-gradient-to-r from-amber-400 to-amber-500'
                                        : userType === USER_TYPES.PREMIUM_STANDARD
                                          ? 'bg-gradient-to-r from-yellow-400 to-yellow-500'
                                          : userType === USER_TYPES.PREMIUM_VIP
                                            ? 'bg-gradient-to-r from-purple-500 to-purple-600'
                                            : 'bg-gray-500'
                                  }`}
                                >
                                  {/* Inner shine effect */}
                                  <div className="absolute inset-0 rounded-full bg-white/20 opacity-50"></div>

                                  {/* Badge text */}
                                  <span className="relative z-10">
                                    {userType === USER_TYPES.MEMBER && 'M'}
                                    {userType === USER_TYPES.PREMIUM_BASIC && 'P'}
                                    {userType === USER_TYPES.PREMIUM_STANDARD && 'S'}
                                    {userType === USER_TYPES.PREMIUM_VIP && 'VIP'}
                                  </span>

                                  {/* Premium sparkle */}
                                  {(userType === USER_TYPES.PREMIUM_STANDARD ||
                                    userType === USER_TYPES.PREMIUM_VIP) && (
                                    <div className="absolute -top-0.5 -right-0.5 size-1.5 rounded-full bg-white animate-ping opacity-75"></div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                          {/* Always render img if avatar_url exists, but handle error gracefully */}
                          {(user.avatar_url || user.avatarUrl) && (
                            <img
                              src={user.avatar_url || user.avatarUrl}
                              alt={user.username}
                              className="size-full rounded-full border-2 border-gray-800 object-cover"
                              crossOrigin="anonymous"
                              referrerPolicy="no-referrer"
                              onError={e => {
                                e.target.style.display = 'none';
                                e.target.nextElementSibling.style.display = 'flex';
                              }}
                              onLoad={e => {
                                e.target.nextElementSibling.style.display = 'none';
                              }}
                            />
                          )}

                          {/* Fallback Avatar - shown when no avatar_url or when img fails to load */}
                          <div
                            className={`absolute inset-0 size-full items-center justify-center rounded-full border-2 border-gray-800 bg-gradient-to-br from-gray-700 to-gray-800 ${
                              user.avatar_url || user.avatarUrl ? 'hidden' : 'flex'
                            }`}
                          >
                            <span className="text-sm font-bold text-white">
                              {user.username?.[0]?.toUpperCase() || '?'}
                            </span>
                          </div>

                          {/* Online Status Indicator */}
                          <div className="absolute -bottom-0.5 -right-0.5 size-3 rounded-full border-2 border-gray-900 bg-green-500 shadow-sm"></div>
                        </div>
                      </div>
                    </IconButton>
                  </Tooltip>
                  <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleProfileMenuClose}
                    PaperProps={{
                      elevation: 0,
                      sx: {
                        overflow: 'visible',
                        filter: 'drop-shadow(0px 8px 32px rgba(0,0,0,0.4))',
                        mt: 1.5,
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '12px',
                        '& .MuiMenuItem-root': {
                          color: '#f3f4f6',
                          padding: '12px 16px',
                          fontSize: '14px',
                          fontWeight: 500,
                          borderRadius: '8px',
                          margin: '4px 8px',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            backgroundColor: '#374151',
                            transform: 'translateX(2px)',
                          },
                          '&:first-of-type': {
                            marginTop: '8px',
                          },
                          '&:last-of-type': {
                            marginBottom: '8px',
                            color: '#ef4444',
                            '&:hover': {
                              backgroundColor: '#fca5a5',
                              color: '#dc2626',
                            },
                          },
                        },
                      },
                    }}
                    transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                    anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  >
                    <MenuItem onClick={handleProfileClick}>
                      <AccountCircle fontSize="small" sx={{ mr: 1.5, color: '#10b981' }} />
                      {t('auth.profile')}
                    </MenuItem>
                    <MenuItem onClick={handleSettingsClick}>
                      <Settings fontSize="small" sx={{ mr: 1.5, color: '#6b7280' }} />
                      {t('auth.settings')}
                    </MenuItem>
                    <MenuItem onClick={handleLogout}>
                      <Logout fontSize="small" sx={{ mr: 1.5 }} />
                      {t('auth.logout')}
                    </MenuItem>
                  </Menu>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate('/login')}
                    className="rounded-md border border-red-600 px-4 py-2 text-red-600 transition-colors hover:bg-red-600 hover:text-white"
                  >
                    {t('auth.signIn')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      {/* Gradient line */}
      <div className="absolute inset-x-0 bottom-0 h-[2px]">
        <div className="size-full bg-gradient-to-r from-transparent via-red-600/40 to-transparent dark:via-red-500/50" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-red-600/20 to-transparent blur-[1px] dark:via-red-500/30" />
      </div>
    </header>
  );
};

export default Header;
