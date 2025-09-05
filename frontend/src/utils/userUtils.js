/**
 * Utility functions để kiểm tra và xử lý user types
 */

/**
 * Kiểm tra xem user có phải là premium user không
 * @param {string} userType - User type từ backend
 * @returns {boolean} true nếu là premium user
 */
export const isPremiumUser = userType => {
  if (!userType) return false;

  const premiumTypes = ['premium_vip', 'premium_pro', 'premium_basic'];

  return premiumTypes.includes(userType);
};

/**
 * Kiểm tra xem user có phải là member user không
 * @param {string} userType - User type từ backend
 * @returns {boolean} true nếu là member user
 */
export const isMemberUser = userType => {
  return userType === 'member';
};

/**
 * Kiểm tra xem user có phải là free user không (chưa đăng ký)
 * @param {string} userType - User type từ backend
 * @returns {boolean} true nếu là free user
 */
export const isFreeUser = userType => {
  return !userType || userType === 'free';
};

/**
 * Lấy display name cho user type
 * @param {string} userType - User type từ backend
 * @returns {string} Display name
 */
export const getUserTypeDisplayName = userType => {
  if (!userType) return 'Free User';

  const displayNames = {
    member: 'Member',
    premium_vip: 'Premium VIP',
    premium_pro: 'Premium Pro',
    premium_basic: 'Premium Basic',
    free: 'Free User',
  };

  return displayNames[userType] || userType;
};

/**
 * Lấy level của user (số càng cao càng premium)
 * @param {string} userType - User type từ backend
 * @returns {number} Level (0: free, 1: member, 2: basic, 3: pro, 4: vip)
 */
export const getUserLevel = userType => {
  if (!userType) return 0;

  const levels = {
    free: 0,
    member: 1,
    premium_basic: 2,
    premium_pro: 3,
    premium_vip: 4,
  };

  return levels[userType] || 0;
};

/**
 * Kiểm tra xem user có quyền truy cập tính năng premium không
 * @param {string} userType - User type từ backend
 * @param {number} requiredLevel - Level tối thiểu cần thiết
 * @returns {boolean} true nếu có quyền truy cập
 */
export const hasPremiumAccess = (userType, requiredLevel = 1) => {
  const userLevel = getUserLevel(userType);
  return userLevel >= requiredLevel;
};

/**
 * Lấy thông tin chi tiết về user type
 * @param {string} userType - User type từ backend
 * @returns {object} Thông tin chi tiết
 */
export const getUserTypeInfo = userType => {
  return {
    type: userType,
    displayName: getUserTypeDisplayName(userType),
    level: getUserLevel(userType),
    isPremium: isPremiumUser(userType),
    isMember: isMemberUser(userType),
    isFree: isFreeUser(userType),
  };
};
