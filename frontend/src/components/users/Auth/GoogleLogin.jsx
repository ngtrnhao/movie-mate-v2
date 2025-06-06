import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { googleLogin } from '../../../store/slices/authSlice';
import authService from '../../../services/auth.service';

const GoogleLogin = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const userData = await authService.googleLogin(response.access_token);
        dispatch(googleLogin(userData));
        navigate('/home');
      } catch (error) {
        console.error('Google login failed:', error);
        // Show error message to user
        alert(error.message || 'Google login failed. Please try again.');
      }
    },
    onError: (error) => {
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
