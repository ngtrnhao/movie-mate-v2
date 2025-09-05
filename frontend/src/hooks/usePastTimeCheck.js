import { useState, useCallback } from 'react';

export const usePastTimeCheck = () => {
  const [isPastTime, setIsPastTime] = useState(false);
  const [pastTimeWarning, setPastTimeWarning] = useState('');

  // Hàm kiểm tra thời gian trong quá khứ
  const checkPastTime = useCallback((date, time) => {
    if (!date || !time) return false;

    const scheduledDateTime = new Date(`${date}T${time}:00`);
    const now = new Date();

    // Thêm buffer 1 phút để tránh lỗi timing
    const bufferTime = new Date(now.getTime() + 60000);

    return scheduledDateTime < bufferTime;
  }, []);

  // Hàm cập nhật warning khi thời gian thay đổi
  const updatePastTimeWarning = useCallback(
    (date, time) => {
      if (!date || !time) {
        setIsPastTime(false);
        setPastTimeWarning('');
        return;
      }

      const isPast = checkPastTime(date, time);
      setIsPastTime(isPast);

      if (isPast) {
        const scheduledDateTime = new Date(`${date}T${time}:00`);
        const now = new Date();
        const diffMinutes = Math.floor((now - scheduledDateTime) / (1000 * 60));

        if (diffMinutes < 60) {
          setPastTimeWarning(`Thời gian đã qua ${diffMinutes} phút. Task sẽ chạy ngay lập tức.`);
        } else if (diffMinutes < 1440) {
          const diffHours = Math.floor(diffMinutes / 60);
          setPastTimeWarning(`Thời gian đã qua ${diffHours} giờ. Task sẽ chạy ngay lập tức.`);
        } else {
          const diffDays = Math.floor(diffMinutes / 1440);
          setPastTimeWarning(`Thời gian đã qua ${diffDays} ngày. Task sẽ chạy ngay lập tức.`);
        }
      } else {
        setPastTimeWarning('');
      }
    },
    [checkPastTime]
  );

  // Hàm xác nhận thời gian trong quá khứ
  const confirmPastTime = useCallback(
    (date, time) => {
      const isPast = checkPastTime(date, time);

      if (isPast) {
        return window.confirm(
          'Thời gian xuất bản đã qua. Task sẽ chạy ngay lập tức. Bạn có muốn tiếp tục?'
        );
      }

      return true;
    },
    [checkPastTime]
  );

  return {
    isPastTime,
    pastTimeWarning,
    checkPastTime,
    updatePastTimeWarning,
    confirmPastTime,
  };
};
