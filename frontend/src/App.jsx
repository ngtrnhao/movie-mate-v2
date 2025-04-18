import './App.css';
import Header from './components/Header/index';
import { ThemeProvider } from './context/ThemeContext';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Footer from './components/footer';
import LandingPage from './pages/Landing';
import HomePage from './pages/Home';
function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <div className="bg-background text-foreground flex min-h-screen flex-col transition-colors duration-200">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route
              path="/*"
              element={
                <>
                  <Header />
                  <main className="flex-1">
                    <Routes>
                      <Route path="/home" element={<HomePage />} />
                    </Routes>
                  </main>
                  <Footer />
                </>
              }
            ></Route>
          </Routes>
        </div>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
