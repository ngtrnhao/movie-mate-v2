import './App.css';
import Header from './components/header';
import { LandingThemeProvider } from './context/LandingThemeContext';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Footer from './components/footer';
import LandingPage from './pages/Landing';
import HomePage from './pages/Home';
import ErrorPage from './pages/error';
import { QueryProvider } from './providers/QueryProvider';

function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <Routes>
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
          <Route
            path="/*"
            element={
              <div className="text-foreground flex min-h-screen flex-col transition-colors duration-200">
                <Header />
                <main className="bg-background flex-1 transition-colors duration-200">
                  <Routes>
                    <Route path="/home" element={<HomePage />} />
                    <Route path="*" element={<ErrorPage />} />
                  </Routes>
                </main>
                <Footer />
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  );
}

export default App;
