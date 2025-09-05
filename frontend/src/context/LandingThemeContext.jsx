import { createContext, useContext } from 'react';

const LandingThemeContext = createContext();

export const LandingThemeProvider = ({ children }) => {
  // Always return dark theme
  const value = {
    isDarkMode: true,
    toggleTheme: () => {}, // Empty function since we don't want to allow theme toggle
  };

  return <LandingThemeContext.Provider value={value}>{children}</LandingThemeContext.Provider>;
};

export const useLandingTheme = () => {
  const context = useContext(LandingThemeContext);
  if (!context) {
    throw new Error('useLandingTheme must be used within a LandingThemeProvider');
  }
  return context;
};
