import { useState } from 'react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../../../store/slices/authSlice';
import { selectAuthLoading, selectAuthError } from '../../../store/selectors/authSelectors';
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

const RegisterForm = () => {
  const { t } = useTranslation('auth');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const loading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);

  const [form, setForm] = useState({ email: '', password: '', confirmPassword: '' });
  const [formError, setFormError] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setFormError({ ...formError, [e.target.name]: '' });
  };
  const validate = () => {
    const errors = {};

    //Username validation
    if (!form.username) {
      errors.username = t('validation.usernameRequired');
    } else if (form.username.length < 3 || form.username.length > 20) {
      errors.username = t('validation.usernameLength');
    }
    //Email validation
    if (!form.email) {
      errors.email = t('validation.emailRequired');
    } else if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      errors.email = t('validation.invalidEmail');
    }
    //Password validation
    if (!form.password) {
      errors.password = t('validation.passwordRequired');
    } else if (form.password.length < 8) {
      errors.password = t('validation.passwordLength');
    }
    //Confirm password validation
    if (!form.confirmPassword) {
      errors.confirmPassword = t('validation.confirmPasswordRequired');
    } else if (form.password !== form.confirmPassword) {
      errors.confirmPassword = t('validation.passwordMismatch');
    }
    return errors;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();

    //Validate form
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFormError(errors);
      return;
    }
    try {
      //Dispatch register action
      const resultAction = await dispatch(
        register({
          username: form.username,
          email: form.email,
          password: form.password,
        })
      );
      if (register.fulfilled.match(resultAction)) {
        //Register successful
        navigate('/login');
      }
    } catch (err) {
      //Error is handled by the reducer
      console.error('Register failed:', err);
    }
  };
  const handleGoogleLogin = () => {
    alert('Google registration coming soon!');
  };
  const handleFacebookLogin = () => {
    alert('Facebook registration coming soon!');
  };
  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl bg-[#18181b] p-8 shadow-xl ">
      <h2 className="mb-2 text-center text-2xl font-bold text-white ">
        {t('signUp.title', 'Create an account')}
      </h2>
      <p className="mb-6 text-center text-gray-400">
        {t('signUp.subtitle', 'Join MovieMate to get started')}
      </p>
      <form onSubmit={handleSubmit} autoComplete="off">
        {/* Username field */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-white " htmlFor="username">
            {t('signUp.username', 'Username')}
          </label>
          <input
            className="placholder:text-gray-400 w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type="text"
            id="username"
            name="username"
            placeholder="justin bieber"
            value={form.username}
            onChange={handleChange}
            autoComplete="username"
          />
          {formError.username && (
            <div className="mt-1 text-sm text-red-500">{formError.username}</div>
          )}
        </div>
        {/* Email field */}
        <div className="mb-4 ">
          <label className="mb-1 block text-sm font-medium text-white " htmlFor="email">
            {t('signUp.email', 'Email')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500 "
            type="email"
            id="email"
            name="email"
            placeholder="your.email@example.com"
            value={form.email}
            onChange={handleChange}
            autoComplete="email"
          ></input>
          {formError.email && <div className="mt-1 text-sm text-red-500">{formError.email}</div>}
        </div>
        {/* Password field */}
        <div className="relative mb-4">
          <label className="mb-1 block text-sm font-medium text-white " htmlFor="password">
            {t('signUp.password', 'Password')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            value={form.password}
            placeholder="********"
            onChange={handleChange}
            autoComplete="new-password"
          ></input>
          <button
            type="button"
            aria-label="Show password"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-9 border-none bg-transparent p-0 text-lg text-gray-400 hover:text-red-500"
            tabIndex={-1}
          >
            {showPassword ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
          </button>
          {formError.password && (
            <div className="mt-1 text-sm text-red-500">{formError.password}</div>
          )}
        </div>
        {/* Confirm password field */}
        <div className="relative mb-4">
          <label className="mb-1 block text-sm font-medium text-white " htmlFor="confirmPassword">
            {t('signUp.confirmPassword', 'Confirm Password')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirmPassword"
            name="confirmPassword"
            placeholder="********"
            value={form.confirmPassword}
            onChange={handleChange}
            autoComplete="new-password"
          ></input>
          <button
            type="button"
            aria-label="Show confirm password"
            onClick={() => setShowConfirmPassword((v) => !v)}
            className="absolute right-3 top-9 border-none bg-transparent p-0 text-lg text-gray-400 hover:text-red-500"
            tabIndex={-1}
          >
            {showConfirmPassword ? (
              <EyeOffIcon className="size-5" />
            ) : (
              <EyeIcon className="size-5" />
            )}
          </button>
          {formError.confirmPassword && (
            <div className="mt-1 text-sm text-red-500">{formError.confirmPassword}</div>
          )}
        </div>
        {error && <div className="mb-2 text-sm text-red-500">{error}</div>}
        <button
          className="mb-4 w-full rounded-lg bg-red-600 py-2.5 text-base font-semibold text-white transition-colors hover:bg-red-700 disabled:bg-gray-500"
          type="submit"
          disabled={loading}
        >
          {loading
            ? t('signUp.loading', 'Creating account...')
            : t('signUp.submit', 'Create account')}
        </button>
        <div className="my-4 flex items-center ">
          <div className="h-px flex-1 bg-gray-700" />
          <span className="mx-3 text-xs text-gray-500">
            {t('signUp.orContinueWith', 'Or conitnue with')}
          </span>
          <div className="h-px flex-1 bg-gray-700" />
        </div>
        <div className="mb-4 flex gap-3">
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-white py-2.5 font-medium text-black transition-colors hover:bg-gray-100"
          >
            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              alt="Google"
              className="size-5"
            />
            Google
          </button>
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
          <span className="text-gray-400">
            {t('signUp.haveAccount', 'Already have an account?')}{' '}
          </span>
          <Link to="/login" className="font-medium text-red-500 hover:text-red-400">
            {t('signUp.login', 'Sign in')}
          </Link>
        </div>
      </form>
    </div>
  );
};
export default RegisterForm;
