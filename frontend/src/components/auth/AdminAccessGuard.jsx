import { useSelector } from 'react-redux';
import {
  selectIsAdmin,
  selectIsModerator,
  selectHasAdminAccess,
} from '../../store/slices/authSlice';
import { Navigate } from 'react-router-dom';

const AdminAccessGuard = ({ children, requiredRole = 'admin' }) => {
  const isAdmin = useSelector(selectIsAdmin);
  const isModerator = useSelector(selectIsModerator);
  const hasAdminAccess = useSelector(selectHasAdminAccess);
  const groups = useSelector(state => state.auth.user?.groups);

  // Debug logs
  console.log(
    '[AdminAccessGuard] isAdmin:',
    isAdmin,
    '| isModerator:',
    isModerator,
    '| hasAdminAccess:',
    hasAdminAccess,
    '| groups:',
    groups
  );

  // Nếu không có quyền admin/moderator, redirect về trang chủ
  if (!hasAdminAccess) {
    console.warn('[AdminAccessGuard] No admin/moderator access, redirecting to /');
    return <Navigate to="/" replace />;
  }

  // Nếu yêu cầu quyền admin nhưng user chỉ là moderator
  if (requiredRole === 'admin' && !isAdmin) {
    console.warn(
      '[AdminAccessGuard] Required admin, but user is not admin. Redirecting to /moderator'
    );
    return <Navigate to="/moderator" replace />;
  }

  // Nếu yêu cầu quyền moderator nhưng user là admin, cho phép truy cập
  if (requiredRole === 'moderator' && isAdmin) {
    return children;
  }

  return children;
};

export default AdminAccessGuard;
