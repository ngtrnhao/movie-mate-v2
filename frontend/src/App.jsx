import './App.css';
import Header from './components/header';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Footer from './components/footer';
import LandingPage from './pages/Landing';
import HomePage from './pages/Home';
import MoviesPage from './pages/Movies';
import ErrorPage from './pages/error';
import { QueryProvider } from './providers/QueryProvider';
import I18nProvider from './i18n/I18nProvider';
import AuthLayout from './layouts/AuthLayout';
import LoginForm from './components/users/Auth/LoginForm';
import RegisterForm from './components/users/Auth/RegisterForm';
import ForgotPasswordForm from './components/users/Auth/ForgotPasswordForm';
import ResetPasswordForm from './components/users/Auth/ResetPasswordForm';
import MovieDetailsPage from './pages/Movies/MovieDetailsPage';
import Recommendation from './pages/recommendation';
import CastMemberDetail from './pages/CastMember';
import VerifyEmail from './pages/VerifyEmail';
import Profile from './pages/Profile';
import ProfileEdit from './pages/Profile/ProfileEdit';
import PrivateRoute from './components/auth/PrivateRoute';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  rehydrateAuth,
  hideProfileCompletionModal,
  selectShowProfileCompletionModal,
} from './store/slices/authSlice';
import ProfileCompletionModal from './components/modals/ProfileCompletionModal';
import EmailVerificationChecker from './components/auth/EmailVerificationChecker';
// import AdManager from './components/ads/AdManager';
import PricingPage from './pages/Pricing';
import CheckoutPage from './pages/Checkout';
import AdminDashboard from './pages/Admin/Dashboard';
import ModeratorDashboard from './pages/Moderator/Dashboard';
import AdminAccessGuard from './components/auth/AdminAccessGuard';
import './utils/testFavorites'; // Import for browser console access
import { Provider } from 'react-redux';
import store from './store';
import { WatchlistProvider } from './context/WatchlistContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Toaster } from 'react-hot-toast';
// import PerformanceMonitor from './components/common/PerformanceMonitor';
// import AdDisplayTest from './components/ads/AdDisplayTest';
// import AdFrequencyStatus from './components/common/AdFrequencyStatus';
// import AdWaitMessage from './components/common/AdWaitMessage';

// Import test utilities for development
// if (process.env.NODE_ENV === 'development') {
//   import('./utils/testAdFrequency').then(({ runAllAdFrequencyTests }) => {
//     window.runAllAdFrequencyTests = runAllAdFrequencyTests;
//   });
// }

// Global error handler để chặn lỗi Script error từ quảng cáo ngoài
if (typeof window !== 'undefined') {
  window.onerror = function (message, source) {
    if (message === 'Script error.') {
      // Lỗi từ script quảng cáo ngoài, chỉ log warning
      console.warn('Script error from third-party script:', source);
      return true; // Ngăn không lan ra app
    }
    // Xử lý lỗi khác như bình thường
    return false;
  };
}

function App() {
  const dispatch = useDispatch();
  const showProfileCompletionModal = useSelector(selectShowProfileCompletionModal);

  // Debug logging for modal state
  useEffect(() => {
    console.log('🔍 App.jsx - showProfileCompletionModal:', showProfileCompletionModal);
  }, [showProfileCompletionModal]);

  // Prevent automatic scroll restoration for better UX
  useEffect(() => {
    // Override browser's scroll restoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
  }, []);

  // Khi app khởi động, gọi rehydrateAuth để khôi phục trạng thái đăng nhập từ localStorage vào Redux
  useEffect(() => {
    dispatch(rehydrateAuth());

    // Dọn dẹp một lần các key localStorage cũ của hệ thống quảng cáo
    const oldAdKeys = [
      'footerAdLastShown',
      'vemAdLastShown',
      'overlayAdLastShown',
      'globalAdShownTimestamps',
    ];

    oldAdKeys.forEach(key => {
      try {
        localStorage.removeItem(key);
      } catch (e) {
        // Bỏ qua lỗi nếu có
      }
    });
  }, [dispatch]);

  // Thiết lập trình xử lý lỗi toàn cục để ngăn chặn lỗi từ script của bên thứ ba làm sập ứng dụng
  useEffect(() => {
    const errorHandler = event => {
      if (event.message.includes('Script error')) {
        console.warn(
          `Caught a third-party script error. Preventing app crash. Message: ${event.message}`
        );
        event.preventDefault();
      }
    };

    const promiseRejectionHandler = event => {
      console.warn(`Caught unhandled promise rejection. Reason:`, event.reason);
    };

    window.addEventListener('error', errorHandler);
    window.addEventListener('unhandledrejection', promiseRejectionHandler);

    // Dọn dẹp các listener khi component bị unmount
    return () => {
      window.removeEventListener('error', errorHandler);
      window.removeEventListener('unhandledrejection', promiseRejectionHandler);
    };
  }, []);

  return (
    <Provider store={store}>
      <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
        <I18nProvider>
          <WatchlistProvider>
            <BrowserRouter>
              <QueryProvider>
                {/* Quản lý quảng cáo popup và interstitial */}
                <div
                  style={{
                    position: 'fixed',
                    bottom: '20px',
                    right: '20px',
                    zIndex: 9999,
                    pointerEvents: 'none',
                  }}
                >
                  {/* <div style={{ pointerEvents: 'auto' }}>
                    <AdManager />
                  </div> */}
                </div>
                <Routes>
                  {/* Landing Page Route */}
                  <Route
                    path="/"
                    element={
                      <div className="flex min-h-screen flex-col text-foreground">
                        <LandingPage />
                      </div>
                    }
                  />

                  {/* Auth Routes */}
                  <Route element={<AuthLayout />}>
                    <Route path="/login" element={<LoginForm />} />
                    <Route path="/register" element={<RegisterForm />} />
                    <Route path="/forgot-password" element={<ForgotPasswordForm />} />
                    <Route path="/reset-password" element={<ResetPasswordForm />} />
                  </Route>

                  {/* Admin Routes - Separate from main layout */}
                  <Route
                    path="/admin"
                    element={
                      <PrivateRoute>
                        <AdminAccessGuard requiredRole="admin">
                          <AdminDashboard />
                        </AdminAccessGuard>
                      </PrivateRoute>
                    }
                  />

                  {/* Moderator Routes - Separate from main layout */}
                  <Route
                    path="/moderator"
                    element={
                      <PrivateRoute>
                        <AdminAccessGuard requiredRole="moderator">
                          <ModeratorDashboard />
                        </AdminAccessGuard>
                      </PrivateRoute>
                    }
                  />

                  {/* Main App Routes */}
                  <Route
                    path="/*"
                    element={
                      <div className="flex min-h-screen flex-col text-foreground transition-colors duration-200">
                        <Header />
                        <main className="flex-1 bg-background transition-colors duration-200">
                          <Routes>
                            <Route path="/home" element={<HomePage />} />
                            <Route path="/movies" element={<MoviesPage />} />
                            <Route path="/movies/:movieId" element={<MovieDetailsPage />} />
                            <Route path="/cast/:castId" element={<CastMemberDetail />} />
                            <Route path="/recommendation" element={<Recommendation />} />
                            <Route path="/verify-email" element={<VerifyEmail />} />
                            <Route path="/pricing" element={<PricingPage />} />
                            <Route
                              path="/checkout"
                              element={
                                <PrivateRoute>
                                  <CheckoutPage />
                                </PrivateRoute>
                              }
                            />
                            <Route
                              path="/profile/:userId"
                              element={
                                <PrivateRoute>
                                  <Profile />
                                </PrivateRoute>
                              }
                            />
                            <Route
                              path="/profile/edit"
                              element={
                                <PrivateRoute>
                                  <ProfileEdit />
                                </PrivateRoute>
                              }
                            />

                            <Route path="*" element={<ErrorPage />} />
                          </Routes>
                        </main>
                        <Footer />
                      </div>
                    }
                  />
                </Routes>

                {/* <PerformanceMonitor /> */}

                {/* Ad Display Test - chỉ hiển thị trong development */}
                {/* <AdDisplayTest /> */}

                {/* Ad Frequency Status - hiển thị cho eligible users */}
                {/* <AdFrequencyStatus /> */}

                {/* Ad Wait Message - hiển thị countdown cho eligible users */}
                {/* <AdWaitMessage /> */}

                {/* Email Verification Checker */}
                <EmailVerificationChecker />

                {/* Profile Completion Modal */}
                <ProfileCompletionModal
                  open={showProfileCompletionModal}
                  onClose={() => dispatch(hideProfileCompletionModal())}
                  onComplete={updatedUser => {
                    console.log('Profile completed:', updatedUser);
                    dispatch(hideProfileCompletionModal());
                  }}
                />
              </QueryProvider>
              <ToastContainer
                position="bottom-right"
                autoClose={3000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="dark"
              />
            </BrowserRouter>
          </WatchlistProvider>
        </I18nProvider>
      </GoogleOAuthProvider>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 2000,
          style: {
            background: '#333',
            color: '#fff',
          },
          success: {
            duration: 2000,
            iconTheme: {
              primary: '#4ade80',
              secondary: '#fff',
            },
          },
          error: {
            duration: 3000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </Provider>
  );
}

export default App;
