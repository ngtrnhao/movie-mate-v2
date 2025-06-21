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
import MovieDetails from './components/movies/movie-details';
import Recommendation from './pages/recommendation';
import VerifyEmail from './pages/VerifyEmail';
import Profile from './pages/Profile';
import PrivateRoute from './components/auth/PrivateRoute';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { rehydrateAuth } from './store/slices/authSlice';
import AdManager from './components/ads/AdManager';
import PricingPage from './pages/Pricing';
import CheckoutPage from './pages/Checkout';
import PerformanceMonitor from './components/common/PerformanceMonitor';

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
  // Khi app khởi động, gọi rehydrateAuth để khôi phục trạng thái đăng nhập từ localStorage vào Redux
  useEffect(() => {
    dispatch(rehydrateAuth());
  }, [dispatch]);

  // Đặt global error handler trong useEffect để luôn được gán lại
  useEffect(() => {
    window.onerror = function (message, source, _lineno, _colno, _error) {
      if (
        message === 'Script error.' ||
        (_error && _error instanceof Event) ||
        (!message && !_error)
      ) {
        console.warn('Script error or unknown error from third-party script:', source);
        return true;
      }
      return false;
    };
  }, []);

  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
      <I18nProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
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
              <div style={{ pointerEvents: 'auto' }}>
                <AdManager />
              </div>
            </div>
            <Routes>
              {/* Landing Page Route */}
              <Route
                path="/"
                element={
                  <div className="text-foreground flex min-h-screen flex-col">
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

              {/* Main App Routes */}
              <Route
                path="/*"
                element={
                  <div className="text-foreground flex min-h-screen flex-col transition-colors duration-200">
                    <Header />
                    <main className="bg-background flex-1 transition-colors duration-200">
                      <Routes>
                        <Route path="/home" element={<HomePage />} />
                        <Route path="/movies" element={<MoviesPage />} />
                        <Route path="/movies/:movieId" element={<MovieDetails />} />
                        <Route path="/recommendation" element={<Recommendation />} />
                        <Route path="/verify-email" element={<VerifyEmail />} />
                        <Route path="/pricing" element={<PricingPage />} />
                        <Route path="/checkout" element={<CheckoutPage />} />
                        <Route
                          path="/profile/:userId"
                          element={
                            <PrivateRoute>
                              <Profile />
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

            {/* Performance Monitor - chỉ hiển thị trong development */}
            <PerformanceMonitor />
          </QueryProvider>
        </BrowserRouter>
      </I18nProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
