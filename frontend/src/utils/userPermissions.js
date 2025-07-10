// User Types
export const USER_TYPES = {
  GUEST: 'guest',
  MEMBER: 'member',
  PREMIUM_BASIC: 'premium_basic',
  PREMIUM_STANDARD: 'premium_standard',
  PREMIUM_VIP: 'premium_vip',
};

// User Limits
export const USER_LIMITS = {
  [USER_TYPES.GUEST]: {
    favorites: 0,
    lists: 0,
    reviews_per_day: 0,
    moods: 0,
    can_edit_reviews: false,
    can_vote_reviews: false,
    can_add_tags: false,
    can_export: false,
    can_compare_friends: false,
    has_ads: true,
    has_priority_support: false,
    has_beta_access: false,
  },
  [USER_TYPES.MEMBER]: {
    favorites: 100, // max movies
    lists: 3, // max lists
    reviews_per_day: 20,
    moods: 5,
    can_edit_reviews: false,
    can_vote_reviews: false,
    can_add_tags: false,
    can_export: false,
    can_compare_friends: false,
    has_ads: true,
    has_priority_support: false,
    has_beta_access: false,
  },
  [USER_TYPES.PREMIUM_BASIC]: {
    favorites: 500,
    lists: 10,
    reviews_per_day: 100,
    moods: 15,
    can_edit_reviews: true,
    can_vote_reviews: true,
    can_add_tags: true,
    can_export: false,
    can_compare_friends: true,
    has_ads: false,
    has_priority_support: false,
    has_beta_access: false,
  },
  [USER_TYPES.PREMIUM_STANDARD]: {
    favorites: 2000,
    lists: 50,
    reviews_per_day: 200,
    moods: 30,
    can_edit_reviews: true,
    can_vote_reviews: true,
    can_add_tags: true,
    can_export: true,
    can_compare_friends: true,
    has_ads: false,
    has_priority_support: true,
    has_beta_access: false,
  },
  [USER_TYPES.PREMIUM_VIP]: {
    favorites: -1, // unlimited
    lists: -1, // unlimited
    reviews_per_day: -1, // unlimited
    moods: -1, // unlimited
    can_edit_reviews: true,
    can_vote_reviews: true,
    can_add_tags: true,
    can_export: true,
    can_compare_friends: true,
    has_ads: false,
    has_priority_support: true,
    has_beta_access: true,
  },
};

// User Badge Configurations
export const USER_BADGES = {
  [USER_TYPES.GUEST]: {
    label: '',
    color: 'gray',
    bgColor: 'bg-gray-500',
    textColor: 'text-gray-500',
    gradientFrom: 'from-gray-500',
    gradientTo: 'to-gray-600',
  },
  [USER_TYPES.MEMBER]: {
    label: 'MEMBER',
    color: 'blue',
    bgColor: 'bg-blue-600',
    textColor: 'text-blue-600',
    gradientFrom: 'from-blue-500',
    gradientTo: 'to-blue-600',
  },
  [USER_TYPES.PREMIUM_BASIC]: {
    label: 'PREMIUM',
    color: 'amber',
    bgColor: 'bg-amber-600',
    textColor: 'text-amber-600',
    gradientFrom: 'from-amber-500',
    gradientTo: 'to-amber-600',
  },
  [USER_TYPES.PREMIUM_STANDARD]: {
    label: 'STANDARD',
    color: 'yellow',
    bgColor: 'bg-yellow-500',
    textColor: 'text-yellow-500',
    gradientFrom: 'from-yellow-400',
    gradientTo: 'to-yellow-600',
  },
  [USER_TYPES.PREMIUM_VIP]: {
    label: 'VIP',
    color: 'purple',
    bgColor: 'bg-purple-600',
    textColor: 'text-purple-600',
    gradientFrom: 'from-purple-500',
    gradientTo: 'to-purple-600',
  },
};

// Helper Functions
export const getUserType = user => {
  if (!user || !user.id) return USER_TYPES.GUEST;

  let userType = user.user_type || USER_TYPES.MEMBER;

  // Normalize user type to match our constants
  if (typeof userType === 'string') {
    userType = userType.toLowerCase().trim();

    // Handle premium variations
    if (userType.includes('premium')) {
      if (userType.includes('basic')) {
        userType = USER_TYPES.PREMIUM_BASIC;
      } else if (userType.includes('standard')) {
        userType = USER_TYPES.PREMIUM_STANDARD;
      } else if (userType.includes('vip')) {
        userType = USER_TYPES.PREMIUM_VIP;
      }
    } else if (userType === 'member') {
      userType = USER_TYPES.MEMBER;
    } else if (userType === 'guest') {
      userType = USER_TYPES.GUEST;
    }
  }

  // Fallback to member if still not valid
  if (!Object.values(USER_TYPES).includes(userType)) {
    userType = USER_TYPES.MEMBER;
  }

  return userType;
};

export const getUserLimits = user => {
  const userType = getUserType(user);
  return USER_LIMITS[userType];
};

export const getUserBadge = user => {
  const userType = getUserType(user);
  const badge = USER_BADGES[userType];

  // Fallback to MEMBER badge if userType is not found
  if (!badge) {
    return USER_BADGES[USER_TYPES.MEMBER];
  }

  return badge;
};

export const canUserPerform = (user, action) => {
  const limits = getUserLimits(user);
  return limits[action] || false;
};

export const getUserLimit = (user, limitType) => {
  const limits = getUserLimits(user);
  return limits[limitType] || 0;
};

export const isUnlimited = limit => {
  return limit === -1;
};

export const formatLimit = (current, max) => {
  if (max === -1) return 'Unlimited';
  if (max === 0) return 'Upgrade required';
  return `${current}/${max}`;
};

export const getRemainingLimit = (current, max) => {
  if (max === -1) return -1; // unlimited
  return Math.max(0, max - current);
};

export const shouldShowUpgrade = (user, feature) => {
  const userType = getUserType(user);
  const limits = getUserLimits(user);

  if (userType === USER_TYPES.GUEST) return true;
  if (userType === USER_TYPES.PREMIUM_VIP) return false;

  return !limits[feature];
};

export const getUpgradeTarget = user => {
  const userType = getUserType(user);

  switch (userType) {
    case USER_TYPES.GUEST:
      return USER_TYPES.MEMBER;
    case USER_TYPES.MEMBER:
      return USER_TYPES.PREMIUM_BASIC;
    case USER_TYPES.PREMIUM_BASIC:
      return USER_TYPES.PREMIUM_STANDARD;
    case USER_TYPES.PREMIUM_STANDARD:
      return USER_TYPES.PREMIUM_VIP;
    default:
      return null;
  }
};

export const getUpgradeMessage = (user, feature) => {
  const target = getUpgradeTarget(user);
  const targetBadge = USER_BADGES[target];

  if (!target || !targetBadge) return '';

  return `Upgrade to ${targetBadge.label} to unlock ${feature}`;
};
