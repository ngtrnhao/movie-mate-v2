import { useSelector } from 'react-redux';
import { selectIsAuthenticated, selectUser, selectIsRehydrated } from '../store/slices/authSlice';
import adFrequencyService from '../services/adFrequencyService';

/**
 * Hook để kiểm tra điều kiện hiển thị quảng cáo
 * Quảng cáo sẽ hiển thị cho:
 * - Người dùng chưa đăng ký (isAuthenticated = false)
 * - Người dùng đã đăng ký nhưng user_type = 'member'
 * - Chỉ sau khi người dùng ở trang web được 15 phút
 * - Tuân theo tần suất và cooldown được thiết lập
 *
 * @returns {object} Object chứa thông tin về việc hiển thị quảng cáo
 */
const useAdDisplay = (adType = null) => {
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);
  const isRehydrated = useSelector(selectIsRehydrated);

  // Chưa rehydrate xong, không hiển thị quảng cáo để tránh race condition
  if (!isRehydrated) {
    return {
      shouldShow: false,
      reason: 'auth_not_rehydrated',
      timeUntilAds: null,
      timeElapsed: null,
    };
  }

  // Hiển thị quảng cáo nếu:
  // 1. Chưa đăng nhập
  // 2. Đã đăng nhập nhưng là member
  const isEligibleUser = !isAuthenticated || user?.user_type === 'member';

  if (!isEligibleUser) {
    return {
      shouldShow: false,
      reason: 'premium_user',
      timeUntilAds: null,
      timeElapsed: null,
    };
  }

  // Kiểm tra thời gian ban đầu (15 phút)
  const hasInitialDelayPassed = adFrequencyService.hasInitialDelayPassed();
  const timeUntilAds = adFrequencyService.getTimeUntilAdsCanShow();
  const timeElapsed = Date.now() - adFrequencyService.sessionStartTime;

  if (!hasInitialDelayPassed) {
    return {
      shouldShow: false,
      reason: 'initial_delay',
      timeUntilAds: timeUntilAds,
      timeElapsed: timeElapsed,
      timeRemaining: Math.ceil(timeUntilAds / 1000 / 60), // Phút
    };
  }

  // Nếu có adType cụ thể, kiểm tra cooldown
  if (adType) {
    const canShowSpecificAd = adFrequencyService.canShowAd(adType);
    const cooldownRemaining = adFrequencyService.getCooldownRemaining(adType);

    if (!canShowSpecificAd) {
      return {
        shouldShow: false,
        reason: 'cooldown_or_limit',
        timeUntilAds: 0,
        timeElapsed: timeElapsed,
        cooldownRemaining: cooldownRemaining,
        timeRemaining: Math.ceil(cooldownRemaining / 1000 / 60), // Phút
      };
    }
  }

  // Tất cả điều kiện đều pass
  return {
    shouldShow: true,
    reason: 'all_conditions_met',
    timeUntilAds: 0,
    timeElapsed: timeElapsed,
    adsShownThisHour: adFrequencyService.adsShownThisHour,
    maxAdsPerHour: adFrequencyService.maxAdsPerHour,
  };
};

export default useAdDisplay;
