import SearchBar from './SearchBar';
import Navigation from './Navigation';
import MovieMateLogo from './Logo';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Avatar, Menu, MenuItem, IconButton, Tooltip } from '@mui/material';
import { AccountCircle, Settings, Logout } from '@mui/icons-material';
import { logout } from '../../store/slices/authSlice';

const Header = () => {
  const { t } = useTranslation('common');
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isScrolled, setIsScrolled] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const user = useSelector((state) => state.auth.user);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleProfileMenuOpen = (event) => {
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
    navigate('/login');
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
          <div className="flex items-center space-x-6">
            <Navigation />
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <Tooltip title={user.username}>
                    <IconButton
                      onClick={handleProfileMenuOpen}
                      size="large"
                      edge="end"
                      aria-label="account of current user"
                      aria-haspopup="true"
                      color="inherit"
                    >
                      {user.avatar_url ? (
                        <Avatar
                          src={user.avatar_url}
                          alt={user.username}
                          sx={{ width: 32, height: 32 }}
                        />
                      ) : (
                        <AccountCircle sx={{ width: 32, height: 32 }} />
                      )}
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
                        filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                        mt: 1.5,
                        '& .MuiAvatar-root': {
                          width: 32,
                          height: 32,
                          ml: -0.5,
                          mr: 1,
                        },
                      },
                    }}
                    transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                    anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  >
                    <MenuItem onClick={handleProfileClick}>
                      <AccountCircle fontSize="small" sx={{ mr: 1 }} />
                      {t('auth.profile')}
                    </MenuItem>
                    <MenuItem onClick={handleSettingsClick}>
                      <Settings fontSize="small" sx={{ mr: 1 }} />
                      {t('auth.settings')}
                    </MenuItem>
                    <MenuItem onClick={handleLogout}>
                      <Logout fontSize="small" sx={{ mr: 1 }} />
                      {t('auth.logout')}
                    </MenuItem>
                  </Menu>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate('/register')}
                    className="rounded-md border border-red-600 px-4 py-2 text-red-600 transition-colors hover:bg-red-600 hover:text-white"
                  >
                    {t('auth.signUp')}
                  </button>
                  <button
                    onClick={() => navigate('/login')}
                    className="rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
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
