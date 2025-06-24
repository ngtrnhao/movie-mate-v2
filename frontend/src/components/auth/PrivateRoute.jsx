import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { CircularProgress } from '@mui/material';

const PrivateRoute = ({ children }) => {
  const location = useLocation();
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const isRehydrated = useSelector(state => state.auth.isRehydrated);

  // Show loading spinner while rehydrating auth state from localStorage
  if (!isRehydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <CircularProgress size={60} thickness={4} />
      </div>
    );
  }

  // Only redirect to login after rehydration is complete and user is not authenticated
  if (!isAuthenticated) {
    // Only save location state if coming from checkout page
    const shouldSaveLocation = location.pathname.includes('/checkout');

    if (shouldSaveLocation) {
      // Redirect to login page and save the attempted url for checkout
      return <Navigate to="/login" state={{ from: location }} replace />;
    } else {
      // For other protected routes, just redirect to login without saving location
      return <Navigate to="/login" replace />;
    }
  }

  return children;
};

export default PrivateRoute;
