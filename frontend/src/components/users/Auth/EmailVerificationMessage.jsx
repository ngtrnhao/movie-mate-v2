import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';

const EmailVerificationMessage = () => {
  const { t } = useTranslation('auth');

  return (
    <div className="mx-auto w-full max-w-sm rounded-2xl bg-[#18181b] p-8 shadow-xl">
      <h2 className="mb-2 text-center text-2xl font-bold text-white">
        {t('signUp.verifyEmail', 'Verify your email')}
      </h2>
      <p className="mb-6 text-center text-gray-400">
        {t(
          'signUp.verifyEmailMessage',
          'We have sent a verification link to your email address. Please check your inbox and click the link to verify your account.'
        )}
      </p>
      <div className="space-y-4">
        <Link
          to="/login"
          className="block w-full rounded-lg bg-red-600 py-2.5 text-center text-base font-semibold text-white transition-colors hover:bg-red-700"
        >
          {t('signUp.backToLogin', 'Back to Login')}
        </Link>
        <p className="text-center text-sm text-gray-400">
          {t('signUp.didntReceiveEmail', "Didn't receive the email?")}{' '}
          <button
            onClick={() => window.location.reload()}
            className="font-medium text-red-500 hover:text-red-400"
          >
            {t('signUp.resendEmail', 'Resend')}
          </button>
        </p>
      </div>
    </div>
  );
};

export default EmailVerificationMessage;
