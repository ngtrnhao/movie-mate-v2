import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { selectUser } from '../../store/slices/authSlice';
import adFrequencyService from '../../services/adFrequencyService';
import { isPremiumUser } from '../../utils/userUtils';

const AdWaitMessage = () => {
  const user = useSelector(selectUser);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [showMessage, setShowMessage] = useState(false);

  const isPremium = isPremiumUser(user?.user_type);
  const isEligibleUser = !isPremium && (user?.user_type === 'member' || !user);

  useEffect(() => {
    if (!isEligibleUser) {
      return;
    }

    const interval = setInterval(() => {
      const status = adFrequencyService.getStatus();

      if (!status.hasInitialDelayPassed) {
        const remaining = status.timeUntilAds;
        setTimeRemaining(remaining);
        setShowMessage(true);
      } else {
        setShowMessage(false);
        setTimeRemaining(null);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isEligibleUser]);

  const formatTime = milliseconds => {
    const minutes = Math.floor(milliseconds / 1000 / 60);
    const seconds = Math.floor((milliseconds / 1000) % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!showMessage || !isEligibleUser) {
    return null;
  }

  return (
    <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2">
      <div className="flex items-center space-x-3 rounded-lg bg-blue-600 px-6 py-3 text-white shadow-lg">
        <div className="text-xl">⏰</div>
        <div>
          <div className="font-medium">Quảng cáo sẽ hiển thị sau:</div>
          <div className="text-2xl font-bold">{formatTime(timeRemaining)}</div>
        </div>
      </div>
    </div>
  );
};

export default AdWaitMessage;
