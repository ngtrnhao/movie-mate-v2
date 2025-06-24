import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { googleLogin } from '../../../store/slices/authSlice';
import { googleLoginAPI } from '../../../api/auth';

const GoogleLogin = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();
  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async response => {
      try {
        const userData = await googleLoginAPI(response.access_token);
        dispatch(googleLogin(userData));

        // Login successful, handle redirect
        console.log('DEBUG Google login: location.state', location.state);

        // Only redirect to saved location if it exists and is valid (from checkout)
        if (
          location.state?.from?.pathname &&
          location.state.from.pathname.includes('/checkout') &&
          !/\/(undefined|null)/.test(location.state.from.pathname)
        ) {
          const redirectTo = location.state.from.pathname + (location.state.from.search || '');
          console.log('DEBUG Google: redirectTo from checkout', redirectTo);
          navigate(redirectTo);
        } else {
          // Default redirect to home for all other cases
          console.log('DEBUG Google: redirectTo default /home');
          navigate('/home');
        }
      } catch (error) {
        console.error('Google login failed:', error);
        alert(error.message || 'Google login failed. Please try again.');
      }
    },
    onError: error => {
      console.error('Google login failed:', error);
      alert('Google login failed. Please try again.');
    },
  });

  return (
    <button
      type="button"
      onClick={() => handleGoogleLogin()}
      className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-white py-2.5 font-medium text-black transition-colors hover:bg-gray-100"
    >
      <img
        src="https://www.svgrepo.com/show/475656/google-color.svg"
        alt="Google"
        className="size-5"
      />
      Google
    </button>
  );
};

export default GoogleLogin;
