/**
 * PropellerAds Service
 * Service này hiện tại không còn quản lý cooldown,
 * vai trò đó đã được chuyển cho adCooldownService.
 * Giữ lại cấu trúc để có thể mở rộng trong tương lai.
 */
class PropellerAdsService {
  constructor() {
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized) {
      return;
    }
    // Logic khởi tạo (nếu có) trong tương lai
    this.isInitialized = true;
    console.log('PropellerAds Service Initialized (no-op)');
  }
}

const propellerAdsService = new PropellerAdsService();
export default propellerAdsService;
