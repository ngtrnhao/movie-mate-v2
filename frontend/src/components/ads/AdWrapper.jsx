// import { memo } from 'react';
// import PropTypes from 'prop-types';
// import useAdDisplay from '../../hooks/useAdDisplay';

// /**
//  * Component wrapper để kiểm tra điều kiện hiển thị quảng cáo
//  * Chỉ render children nếu người dùng chưa đăng ký hoặc là member
//  */
// const AdWrapper = memo(({ children, fallback = null }) => {
//   const shouldShowAds = useAdDisplay();

//   // Hiển thị quảng cáo nếu điều kiện phù hợp
//   if (shouldShowAds) {
//     return <>{children}</>;
//   }

//   // Hiển thị fallback nếu không nên hiển thị quảng cáo
//   return <>{fallback}</>;
// });

// AdWrapper.propTypes = {
//   children: PropTypes.node.isRequired,
//   fallback: PropTypes.node,
// };

// AdWrapper.displayName = 'AdWrapper';

// export default AdWrapper;
