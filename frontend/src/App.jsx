import './App.css';
import Header from './components/Header';
import { ThemeProvider } from './context/ThemeContext';
import { BrowserRouter } from 'react-router-dom';
import Footer from './components/footer';

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <div className="bg-background text-foreground flex min-h-screen flex-col transition-colors duration-200">
          <Header />
          <Footer />
        </div>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
