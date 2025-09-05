import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { login, setRememberMe } from '../../../store/slices/authSlice';
import {
  selectAuthLoading,
  selectAuthError,
  selectRememberMe,
} from '../../../store/selectors/authSelectors';
import GoogleLogin from './GoogleLogin';

// Heroicons v2 Eye
const EyeIcon = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className={className}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M2.25 12C3.5 7.5 7.5 4.5 12 4.5c4.5 0 8.5 3 9.75 7.5-1.25 4.5-5.25 7.5-9.75 7.5-4.5 0-8.5-3-9.75-7.5z"
    />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

// Heroicons v2 Eye Off
const EyeOffIcon = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className={className}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M3 3l18 18M10.477 10.477A3 3 0 0112 9c1.657 0 3 1.343 3 3 0 .512-.122.995-.338 1.418M6.53 6.53C4.06 8.5 2.25 12 2.25 12c1.25 4.5 5.25 7.5 9.75 7.5 1.61 0 3.13-.38 4.44-1.06M17.47 17.47C19.94 15.5 21.75 12 21.75 12c-1.25-4.5-5.25-7.5-9.75-7.5-1.61 0-3.13.38-4.44 1.06"
    />
  </svg>
);

const LoginForm = () => {
  const { t } = useTranslation('auth');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  // Get state from Redux
  const loading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);
  const rememberMe = useSelector(selectRememberMe);

  // Local form state
  const [form, setForm] = useState({ email: '', password: '' });
  const [formError, setFormError] = useState({});
  const [showPassword, setShowPassword] = useState(false);

  // Handle input change
  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setFormError({ ...formError, [e.target.name]: '' });
  };

  // Handle remember me checkbox
  const handleRememberMe = e => {
    dispatch(setRememberMe(e.target.checked));
  };

  // Form validation
  const validate = () => {
    const errors = {};
    if (!form.email) {
      errors.email = t('validation.emailRequired');
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      errors.email = t('validation.invalidEmail');
    }
    if (!form.password) {
      errors.password = t('validation.passwordRequired');
    } else if (form.password.length < 6) {
      errors.password = t('validation.passwordLength');
    }
    return errors;
  };

  // Handle form submission
  const handleSubmit = async e => {
    e.preventDefault();

    // Validate form
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFormError(errors);
      return;
    }

    try {
      // Dispatch login action
      const resultAction = await dispatch(
        login({
          email: form.email,
          password: form.password,
          rememberMe,
        })
      );

      if (login.fulfilled.match(resultAction)) {
        // Login successful

        // Only redirect to saved location if it exists and is valid (from checkout)
        if (
          location.state?.from?.pathname &&
          location.state.from.pathname.includes('/checkout') &&
          !/\/(undefined|null)/.test(location.state.from.pathname)
        ) {
          const redirectTo = location.state.from.pathname + (location.state.from.search || '');
          navigate(redirectTo);
        } else {
          // Default redirect to home for all other cases
          navigate('/');
        }
      }
    } catch (err) {
      // Error is handled by the reducer
      console.error(t('signIn.error'), err);
    }
  };

  // Social login handlers (placeholders)
  const handleFacebookLogin = () => {
    alert('Facebook login coming soon!');
  };

  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl bg-[#18181b] p-8 shadow-xl">
      <h2 className="mb-2 text-center text-2xl font-bold text-white">
        {t('signIn.title', 'Welcome back')}
      </h2>
      <p className="mb-6 text-center text-gray-400">
        {t('signIn.subtitle', 'Sign in to your account to continue')}
      </p>
      <form onSubmit={handleSubmit} autoComplete="off">
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="email">
            {t('signIn.email', 'Email')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type="email"
            id="email"
            name="email"
            placeholder="your.email@example.com"
            value={form.email}
            onChange={handleChange}
            autoComplete="username"
          />
          {formError.email && <div className="mt-1 text-sm text-red-500">{formError.email}</div>}
        </div>
        <div className="relative mb-4">
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="password">
            {t('signIn.password', 'Password')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            placeholder="********"
            value={form.password}
            onChange={handleChange}
            autoComplete="current-password"
          />
          <button
            type="button"
            aria-label="Show password"
            onClick={() => setShowPassword(v => !v)}
            className="absolute right-3 top-9 border-none bg-transparent p-0 text-lg text-gray-400 hover:text-red-500"
            tabIndex={-1}
          >
            {showPassword ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
          </button>
          <Link
            to="/forgot-password"
            className="absolute right-0 top-0 text-xs font-medium text-red-500 hover:text-red-400"
          >
            {t('signIn.forgotPassword', 'Forgot password?')}
          </Link>
          {formError.password && (
            <div className="mt-1 text-sm text-red-500">{formError.password}</div>
          )}
        </div>
        <div className="mb-4 flex items-center">
          <input
            className="mr-2 size-4 accent-red-600"
            type="checkbox"
            id="rememberMe"
            checked={rememberMe}
            onChange={handleRememberMe}
          />
          <label htmlFor="rememberMe" className="select-none text-sm text-gray-400">
            {t('signIn.rememberMe', 'Remember me for 30 days')}
          </label>
        </div>
        {error && <div className="mb-2 text-center text-sm text-red-500">{error}</div>}
        <button
          className="mb-4 w-full rounded-lg bg-red-600 py-2.5 text-base font-semibold text-white transition-colors hover:bg-red-700"
          type="submit"
          disabled={loading}
        >
          {loading ? t('signIn.loading', 'Signing in...') : t('signIn.submit', 'Sign in')}
        </button>
        <div className="my-4 flex items-center">
          <div className="h-px flex-1 bg-gray-700" />
          <span className="mx-3 text-xs text-gray-500">
            {t('signIn.orContinueWith', 'Or continue with')}
          </span>
          <div className="h-px flex-1 bg-gray-700" />
        </div>
        <div className="mb-4 flex gap-3">
          <GoogleLogin />
          <button
            type="button"
            onClick={handleFacebookLogin}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-[#1877f3] py-2.5 font-medium text-white transition-colors hover:bg-[#145db2]"
          >
            <img
              src="https://www.svgrepo.com/show/475647/facebook-color.svg"
              alt="Facebook"
              className="size-5"
            />
            Facebook
          </button>
        </div>
        <div className="mt-2 text-center">
          <span className="text-gray-400">{t('signIn.noAccount', "Don't have an account?")} </span>
          <Link to="/register" className="font-medium text-red-500 hover:text-red-400">
            {t('signIn.register', 'Sign up')}
          </Link>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;
