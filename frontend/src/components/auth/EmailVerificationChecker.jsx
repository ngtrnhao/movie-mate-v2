import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { checkAndShowProfileModal } from '../../store/slices/authSlice';
import { getProfileCompletionStatusAPI } from '../../api/profileService';

const EmailVerificationChecker = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector(state => state.auth);

  useEffect(() => {
    const checkEmailVerificationAndProfile = async () => {
      if (!isAuthenticated || !user) {
        return;
      }

      try {
        // Check if user's email verification status has changed
        const response = await getProfileCompletionStatusAPI();

        if (response.status === 'success') {
          const { is_email_verified, is_profile_complete, profile_completion_percentage } =
            response.data;

          // Update user data if email verification status changed
          if (user.isEmailVerified !== is_email_verified) {
            // Update user data in Redux
            dispatch({
              type: 'auth/updateUser',
              payload: {
                isEmailVerified: is_email_verified,
                is_profile_complete,
                profile_completion_percentage,
              },
            });
          }

          // Check if we should show profile completion modal
          dispatch(checkAndShowProfileModal());
        }
      } catch (error) {
        console.error('Error checking email verification status:', error);
      }
    };

    // Check immediately when component mounts
    checkEmailVerificationAndProfile();

    // Set up interval to check periodically (every 30 seconds)
    const interval = setInterval(checkEmailVerificationAndProfile, 30000);

    return () => clearInterval(interval);
  }, [dispatch, isAuthenticated, user]);

  // This component doesn't render anything
  return null;
};

export default EmailVerificationChecker;
