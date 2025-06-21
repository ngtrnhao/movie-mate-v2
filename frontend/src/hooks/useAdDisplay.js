import { useSelector } from 'react-redux';
import { selectIsAuthenticated, selectUser, selectIsRehydrated } from '../store/slices/authSlice';

/**
 * Hook để kiểm tra điều kiện hiển thị quảng cáo
 * Quảng cáo sẽ hiển thị cho:
 * - Người dùng chưa đăng ký (isAuthenticated = false)
 * - Người dùng đã đăng ký nhưng user_type = 'member'
 *
 * Sẽ không hiển thị quảng cáo cho đến khi auth state được rehydrate xong.
 *
 * @returns {boolean} true nếu nên hiển thị quảng cáo
 */
const useAdDisplay = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);
  const isRehydrated = useSelector(selectIsRehydrated);

  // Chưa rehydrate xong, không hiển thị quảng cáo để tránh race condition
  if (!isRehydrated) {
    return false;
  }

  // Hiển thị quảng cáo nếu:
  // 1. Chưa đăng nhập
  // 2. Đã đăng nhập nhưng là member
  const shouldShowAds = !isAuthenticated || user?.user_type === 'member';

  return shouldShowAds;
};

export default useAdDisplay;
