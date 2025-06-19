# Hướng dẫn tích hợp PropellerAds vào Movie Mate

## Tổng quan

Tài liệu này hướng dẫn cách tích hợp quảng cáo từ PropellerAds vào ứng dụng Movie Mate. Hệ thống đã được thiết kế để hỗ trợ nhiều loại quảng cáo khác nhau và có thể tùy chỉnh dễ dàng.

## Các loại quảng cáo được hỗ trợ

### 1. Banner Ads

- **BANNER_TOP**: Quảng cáo banner ở đầu trang
- **BANNER_SIDEBAR**: Quảng cáo banner ở sidebar
- **BANNER_FOOTER**: Quảng cáo banner ở footer

### 2. Content Ads

- **CONTENT_TOP**: Quảng cáo nội dung ở đầu
- **CONTENT_MIDDLE**: Quảng cáo nội dung ở giữa
- **CONTENT_BOTTOM**: Quảng cáo nội dung ở cuối

### 3. Popup/Interstitial Ads

- **POPUP**: Quảng cáo popup
- **INTERSTITIAL**: Quảng cáo interstitial

### 4. Video Ads

- **VIDEO**: Quảng cáo video

## Cài đặt

### Bước 1: Tạo tài khoản PropellerAds

1. Truy cập [PropellerAds](https://propellerads.com)
2. Đăng ký tài khoản mới
3. Xác minh email và thông tin tài khoản

### Bước 2: Tạo Zone IDs

1. Đăng nhập vào PropellerAds Dashboard
2. Tạo các zone mới cho từng loại quảng cáo:
   - Banner zones (728x90, 300x250, etc.)
   - Content zones
   - Popup zones
   - Interstitial zones

### Bước 3: Cấu hình Environment Variables

Tạo file `.env` trong thư mục `frontend/` và thêm các Zone ID:

```env
# PropellerAds Configuration
REACT_APP_PROPELLER_ZONE_BANNER_TOP=your_banner_top_zone_id
REACT_APP_PROPELLER_ZONE_BANNER_SIDEBAR=your_banner_sidebar_zone_id
REACT_APP_PROPELLER_ZONE_BANNER_FOOTER=your_banner_footer_zone_id
REACT_APP_PROPELLER_ZONE_CONTENT_TOP=your_content_top_zone_id
REACT_APP_PROPELLER_ZONE_CONTENT_MIDDLE=your_content_middle_zone_id
REACT_APP_PROPELLER_ZONE_CONTENT_BOTTOM=your_content_bottom_zone_id
REACT_APP_PROPELLER_ZONE_POPUP=your_popup_zone_id
REACT_APP_PROPELLER_ZONE_INTERSTITIAL=your_interstitial_zone_id
REACT_APP_PROPELLER_ZONE_VIDEO=your_video_zone_id
```

### Bước 4: Khởi động ứng dụng

```bash
cd frontend
npm install
npm start
```

## Cách sử dụng

### 1. Sử dụng component có sẵn

```jsx
import AdBannerTop from './components/ads/AdBannerTop';
import AdContent from './components/ads/AdContent';
import AdBannerFooter from './components/ads/AdBannerFooter';

// Trong component của bạn
<AdBannerTop />
<AdContent position="TOP" />
<AdBannerFooter />
```

### 2. Sử dụng hook tùy chỉnh

```jsx
import usePropellerAds from './hooks/usePropellerAds';
import PropellerAdsBanner from './components/common/PropellerAdsBanner';

const MyComponent = () => {
  const { getAdConfig, trackEvent } = usePropellerAds('BANNER_TOP');

  const adConfig = getAdConfig({
    style: { minHeight: '120px' },
    onAdClick: () => console.log('Ad clicked!'),
  });

  return <PropellerAdsBanner {...adConfig} />;
};
```

### 3. Sử dụng service trực tiếp

```jsx
import propellerAdsService from './services/propellerAdsService';

// Khởi tạo service
await propellerAdsService.init();

// Hiển thị popup
propellerAdsService.showPopup();

// Track sự kiện
propellerAdsService.trackEvent('BANNER_TOP', 'click', { timestamp: Date.now() });
```

## Cấu trúc thư mục

```
frontend/src/
├── components/
│   ├── ads/
│   │   ├── AdBannerTop.jsx
│   │   ├── AdBannerSidebar.jsx
│   │   ├── AdBannerFooter.jsx
│   │   ├── AdContent.jsx
│   │   └── AdManager.jsx
│   └── common/
│       └── PropellerAdsBanner.jsx
├── hooks/
│   └── usePropellerAds.js
├── services/
│   └── propellerAdsService.js
└── pages/
    └── Home/
        └── index.jsx (đã tích hợp quảng cáo)
```

## Tính năng

### 1. Responsive Design

- Tự động phát hiện device (mobile/desktop)
- Sử dụng zone phù hợp cho từng device
- Responsive layout cho quảng cáo

### 2. Analytics & Tracking

- Track các sự kiện: load, click, error
- Tích hợp với Google Analytics
- Lưu trữ thống kê trong memory

### 3. Performance Optimization

- Lazy loading quảng cáo
- Chỉ load trong production
- Placeholder trong development

### 4. User Experience

- Popup hiển thị sau 5 giây
- Interstitial hiển thị khi scroll 50%
- Không spam quảng cáo

## Tùy chỉnh

### 1. Thay đổi vị trí quảng cáo

```jsx
// Thêm quảng cáo vào bất kỳ component nào
import AdContent from './components/ads/AdContent';

<AdContent position="MIDDLE" className="my-custom-class" />;
```

### 2. Tùy chỉnh style

```jsx
const adConfig = propellerAdsService.getAdConfig('BANNER_TOP', {
  style: {
    minHeight: '120px',
    margin: '20px 0',
    borderRadius: '8px',
  },
});
```

### 3. Thêm event handlers

```jsx
const adConfig = propellerAdsService.getAdConfig('BANNER_TOP', {
  onAdLoad: data => console.log('Ad loaded:', data),
  onAdClick: data => console.log('Ad clicked:', data),
  onAdError: error => console.error('Ad error:', error),
});
```

## Troubleshooting

### 1. Quảng cáo không hiển thị

- Kiểm tra Zone ID trong .env file
- Đảm bảo đang ở production mode
- Kiểm tra console để xem lỗi

### 2. Quảng cáo hiển thị sai vị trí

- Kiểm tra CSS styles
- Đảm bảo container có đủ space
- Kiểm tra responsive breakpoints

### 3. Performance issues

- Kiểm tra network tab
- Đảm bảo quảng cáo không block rendering
- Sử dụng lazy loading

## Best Practices

### 1. User Experience

- Không spam quảng cáo
- Đặt quảng cáo ở vị trí phù hợp
- Responsive design

### 2. Performance

- Lazy load quảng cáo
- Sử dụng async loading
- Optimize bundle size

### 3. Analytics

- Track tất cả events
- Monitor performance
- A/B test vị trí quảng cáo

## Support

Nếu gặp vấn đề, vui lòng:

1. Kiểm tra console logs
2. Xem documentation của PropellerAds
3. Liên hệ support team

## Changelog

### v1.0.0

- Tích hợp cơ bản PropellerAds
- Hỗ trợ banner, content, popup ads
- Analytics và tracking
- Responsive design
