import './App.css';
import Header from './components/header';
import { LandingThemeProvider } from './context/LandingThemeContext';
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
// import ResetPasswordForm from './components/users/Auth/ResetPasswordForm';
import MovieDetails from './components/movies/movie-details';
import Recommendation from './pages/recommendation';

function App() {
  return (
    <I18nProvider>
      <BrowserRouter>
        <QueryProvider>
          <Routes>
            {/* Landing Page Route */}
            <Route
              path="/"
              element={
                <LandingThemeProvider>
                  <div className="text-foreground flex min-h-screen flex-col">
                    <LandingPage />
                  </div>
                </LandingThemeProvider>
              }
            />

            {/* Auth Routes */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginForm />} />
              <Route path="/register" element={<RegisterForm />} />
              <Route path="/forgot-password" element={<ForgotPasswordForm />} />
              {/* <Route path="/reset-password" element={<ResetPasswordForm />} /> */}
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
                      <Route path="*" element={<ErrorPage />} />
                    </Routes>
                  </main>
                  <Footer />
                </div>
              }
            />
          </Routes>
        </QueryProvider>
      </BrowserRouter>
    </I18nProvider>
  );
}

export default App;
