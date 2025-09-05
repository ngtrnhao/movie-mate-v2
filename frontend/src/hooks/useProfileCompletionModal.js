import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { checkAndShowProfileModal } from '../store/slices/authSlice';

export const useProfileCompletionModal = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector(state => state.auth);
  const showModal = useSelector(state => state.auth.showProfileCompletionModal);

  // Check if modal should be shown based on current conditions
  const shouldShowModal = () => {
    if (!isAuthenticated || !user) {
      return false;
    }

    // Only show modal if:
    // 1. User is authenticated
    // 2. Email is verified
    // 3. Profile is not complete
    // 4. Profile completion percentage is less than 80%
    return (
      user.is_email_verified && // Use snake_case only
      !user.is_profile_complete &&
      user.profile_completion_percentage < 80
    );
  };

  // Check and update modal visibility
  const checkModalVisibility = () => {
    dispatch(checkAndShowProfileModal());
  };

  // Check modal visibility when user data changes
  useEffect(() => {
    if (isAuthenticated && user) {
      checkModalVisibility();
    }
  }, [
    isAuthenticated,
    user?.is_email_verified, // Use snake_case only
    user?.is_profile_complete,
    user?.profile_completion_percentage,
  ]);

  return {
    showModal,
    shouldShowModal: shouldShowModal(),
    checkModalVisibility,
    user,
    isAuthenticated,
  };
};
