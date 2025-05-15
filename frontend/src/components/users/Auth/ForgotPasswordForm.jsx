import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { forgotPassword, clearError } from '../../../store/slices/authSlice';
import { selectAuthLoading, selectAuthError } from '../../../store/selectors/authSelectors';
const ForgotPasswordForm = () => {
  const { t } = useTranslation('auth');
  const dispatch = useDispatch();
  const loading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);

  const [email, setEmail] = useState('');
  const [formError, setFormError] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);
  const validate = () => {
    const errors = {};
    if (!email) {
      errors.email = t('validation.emailRequired', 'Email is required');
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
      errors.email = t('validation.invalidEmail', 'Invalid email address');
    }
    return errors;
  };
  const handleChange = (e) => {
    const { value } = e.target;
    setEmail(value);
    setFormError((prev) => ({ ...prev, email: '' }));
    if (error) {
      dispatch(clearError());
    }
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError({});
    dispatch(clearError());
    const errors = validate();
    if (Object.keys(errors).length > 0) {
      setFormError(errors);
      return;
    }
    try {
      const resultAction = await dispatch(forgotPassword({ email }));
      if (forgotPassword.fulfilled.match(resultAction)) {
        dispatch(clearError());
        setIsSubmitted(true);
      }
    } catch (err) {
      console.error('Forgot password failed', err);
    }
  };
  if (isSubmitted) {
    return (
      <div className="mx-auto w-full max-w-sm rounded-lg bg-[#18181b] p-8 shadow-xl">
        <h2 className="mb-2 text-center text-2xl font-bold text-white">
          {t('forgotPassword.checkEmail', 'Check your email')}
        </h2>
        <p className="mb-6 text-center text-sm text-gray-400">
          {t(
            'forgotPassword.instructions',
            'We have sent password reset instructions to your email '
          )}
        </p>
        <Link
          to="/login"
          className="block w-full rounded-lg bg-red-600 py-2.5 text-center text-base font-semibold text-white transition-colors hover:bg-red-700 "
        >
          {t('forgotPassword.backToLogin', 'Back to login ')}
        </Link>
      </div>
    );
  }
  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl bg-[#18181a] p-8 shadow-xl">
      <h2 className="mb-2 text-center text-gray-400">
        {t('forgotPassword.title', 'Forgot Password')}
      </h2>
      <form onSubmit={handleSubmit} autoComplete="off">
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-white " htmlFor="email">
            {t('forgotPassword.email', 'Email')}
          </label>
          <input
            className="w-full rounded-lg border border-[#27272a] bg-[#232326] px-3 py-2 text-white outline-none placeholder:text-gray-400 focus:border-red-500 focus:ring-1 focus:ring-red-500"
            type="email"
            id="email"
            value={email}
            onChange={handleChange}
            placeholder="your.email@example.com"
            autoComplete="email"
          ></input>
          {formError.email && <div className="mt-1 text-sm text-red-500">{formError.email}</div>}
        </div>
        {error && (
          <div className="mb-2 text-sm text-red-500">
            {t('forgotPassword.error', 'Error sending reset email')}
          </div>
        )}
        <button
          className="mb-4 w-full rounded-lg bg-red-600 py-2.5 text-base font-semibold text-white transition-colors hover:bg-red-700 disabled:bg-gray-500"
          type="submit"
          disabled={loading}
        >
          {loading
            ? t('forgotPassword.loading', 'Sending...')
            : t('forgotPassword.sendResetLink', 'Send Reset Link')}
        </button>
        <div className="mt-2 text-center">
          <Link to="/login" className="font-medium text-red-500 hover:text-red-400">
            {t('forgotPassword.backToLogin', 'Back to login')}
          </Link>
        </div>
      </form>
    </div>
  );
};

export default ForgotPasswordForm;
