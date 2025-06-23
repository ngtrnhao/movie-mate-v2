/**
 * Utility để test hệ thống tần suất quảng cáo
 * Chỉ sử dụng trong development
 */
export const testAdFrequency = () => {
  if (process.env.NODE_ENV !== 'development') {
    console.warn('Ad frequency test only available in development');
    return;
  }

  console.log('🧪 Testing ad frequency system...');

  const status = window.adFrequencyService.getStatus();
  console.log('Current status:', status);

  console.log('🧪 Ad frequency test completed');
};

/**
 * Test reset session
 */
export const testResetSession = () => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.log('🧪 Testing session reset...');
  window.adFrequencyService.resetSession();
  console.log('Session reset completed');
};

/**
 * Test canShowAd cho các loại quảng cáo khác nhau
 */
export const testCanShowAds = () => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.log('🧪 Testing canShowAd for different ad types...');

  const adTypes = [
    'banner_top',
    'banner_sidebar',
    'banner_footer',
    'popup',
    'script_loader_overlay',
  ];

  adTypes.forEach(adType => {
    const canShow = window.adFrequencyService.canShowAd(adType);
    const cooldownRemaining = window.adFrequencyService.getCooldownRemaining(adType);

    console.log(`${adType}:`, {
      canShow,
      cooldownRemaining: Math.ceil(cooldownRemaining / 1000 / 60) + ' minutes',
    });
  });
};

/**
 * Test recordAdShown
 */
export const testRecordAdShown = (adType = 'banner_top') => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.log(`🧪 Testing recordAdShown for ${adType}...`);
  window.adFrequencyService.recordAdShown(adType);

  const status = window.adFrequencyService.getStatus();
  console.log('Updated status:', {
    adsShownThisHour: status.adsShownThisHour,
    lastAdShown: status.lastAdShown[adType],
  });
};

/**
 * Test tất cả các function
 */
export const runAllAdFrequencyTests = () => {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.log('🧪 Running all ad frequency tests...');

  testAdFrequency();
  testCanShowAds();

  console.log('🧪 All ad frequency tests completed');
};

// Thêm vào window object để có thể gọi từ console
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  window.testAdFrequency = testAdFrequency;
  window.testResetSession = testResetSession;
  window.testCanShowAds = testCanShowAds;
  window.testRecordAdShown = testRecordAdShown;
  window.runAllAdFrequencyTests = runAllAdFrequencyTests;
}
