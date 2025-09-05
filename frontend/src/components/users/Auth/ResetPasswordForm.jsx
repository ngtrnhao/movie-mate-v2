import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { resetPassword, clearError } from '../../../store/slices/authSlice';
import { selectAuthLoading, selectAuthError } from '../../../store/selectors/authSelectors';

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

const ResetPasswordForm = () => {
  const { t } = useTranslation('auth');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);

  const [form, setForm] = useState({
    password: '',
    confirmPassword: '',
  });
  const [formError, setFormError] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const validate = () => {
    const errors = {};
    if (!form.password) {
      errors.password = t('validation.passwordRequired', 'Password is required');
    } else if (form.password.length < 6) {
      errors.password = t('validation.passwordLength', 'Password must be at least 6 characters');
    }

    if (!form.confirmPassword) {
      errors.confirmPassword = t(
        'validation.confirmPasswordRequired',
        'Please confirm your password'
      );
    } else if (form.password !== form.confirmPassword) {
      errors.confirmPassword = t('validation.passwordMismatch', 'Passwords do not match');
    }

    return errors;
  };

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    setFormError(prev => ({ ...prev, [name]: '' }));
    if (error) {
      dispatch(clearError());
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setFormError({});
    dispatch(clearError());

    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFormError(errors);
      return;
    }

    const token = searchParams.get('token');
    if (!token) {
      setFormError({
        general: t('resetPassword.invalidToken', 'Invalid reset link. Please request a new one.'),
      });
      return;
    }

    try {
      const resultAction = await dispatch(
        resetPassword({
          token,
          password: form.password,
          confirm_password: form.confirmPassword,
        })
      );

      if (resetPassword.fulfilled.match(resultAction)) {
        setIsSubmitted(true);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      }
    } catch (err) {
      console.error('Reset password failed:', err);
    }
  };

  if (isSubmitted) {
    return (
      <div className="mx-auto w-full max-w-sm rounded-lg bg-[#18181b] p-8 shadow-xl">
        <h2 className="mb-2 text-center text-2xl font-bold text-white">
          {t('resetPassword.success', 'Password Reset Successful')}
        </h2>
        <p className="mb-6 text-center text-sm text-gray-400">
          {t(
            'resetPassword.redirectMessage',
            'Your password has been reset successfully. Redirecting to login...'
          )}
        </p>
        <Link
          to="/login"
          className="block w-full rounded-lg bg-red-600 py-2.5 text-center text-base font-semibold text-white transition-colors hover:bg-red-700"
        >
          {t('resetPassword.backToLogin', 'Back to Login')}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl bg-[#18181a] p-8 shadow-xl">
      <h2 className="mb-2 text-center text-gray-400">
        {t('resetPassword.title', 'Reset Password')}
      </h2>
      <form onSubmit={handleSubmit} autoComplete="off">
        <div className="relative mb-4">
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="password">
            {t('resetPassword.password', 'New Password')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="********"
            autoComplete="new-password"
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
          {formError.password && (
            <div className="mt-1 text-sm text-red-500">{formError.password}</div>
          )}
        </div>

        <div className="relative mb-4">
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="confirmPassword">
            {t('resetPassword.confirmPassword', 'Confirm New Password')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-4 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirmPassword"
            name="confirmPassword"
            value={form.confirmPassword}
            onChange={handleChange}
            placeholder="********"
            autoComplete="new-password"
          />
          <button
            type="button"
            aria-label="Show confirm password"
            onClick={() => setShowConfirmPassword(v => !v)}
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

        {formError.general && (
          <div className="mb-2 text-center text-sm text-red-500">{formError.general}</div>
        )}
        {error && (
          <div className="mb-2 text-center text-sm text-red-500">
            {t('resetPassword.error', 'Error resetting password')}
          </div>
        )}

        <button
          className="mb-4 w-full rounded-lg bg-red-600 py-2.5 text-base font-semibold text-white transition-colors hover:bg-red-700 disabled:bg-gray-500"
          type="submit"
          disabled={loading}
        >
          {loading
            ? t('resetPassword.loading', 'Resetting...')
            : t('resetPassword.submit', 'Reset Password')}
        </button>

        <div className="mt-2 text-center">
          <Link to="/login" className="font-medium text-red-500 hover:text-red-400">
            {t('resetPassword.backToLogin', 'Back to Login')}
          </Link>
        </div>
      </form>
    </div>
  );
};

export default ResetPasswordForm;
