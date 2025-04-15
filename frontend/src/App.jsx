import './App.css';
import Header from './Components/Header';
import { ThemeProvider } from './context/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-white text-gray-900 transition-colors duration-200 dark:bg-gray-900 dark:text-white">
        <Header />
      </div>
    </ThemeProvider>
  );
}

export default App;
