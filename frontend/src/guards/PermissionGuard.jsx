import { useSelector } from 'react-redux';
import PropTypes from 'prop-types';

/**
 * A component that renders its children only if the current user's role
 * is included in the allowedRoles prop.
 *
 * @param {object} props - The component props.
 * @param {React.ReactNode} props.children - The content to render if the user has permission.
 * @param {string[]} props.allowedRoles - An array of user types that are allowed to see the content.
 * @returns {React.ReactNode|null} The children if the user has permission, otherwise null.
 */
const PermissionGuard = ({ children, allowedRoles }) => {
  const userType = useSelector(state => state.auth.user.user_type);
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);

  // User must be authenticated and their role must be in the allowed list
  const hasPermission = isAuthenticated && allowedRoles.includes(userType);

  return hasPermission ? <>{children}</> : null;
};

PermissionGuard.propTypes = {
  children: PropTypes.node.isRequired,
  allowedRoles: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default PermissionGuard;
