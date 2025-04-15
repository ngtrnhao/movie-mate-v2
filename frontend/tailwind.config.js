/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: '#E50914',
        'brand-dark': '#B81D24',
        'brand-light': '#F40612',
        // Theme toggle colors
        'toggle-light': '#2F2F2F',
        'toggle-dark': '#E5E5E5',
        'toggle-hover-light': '#F5F5F5',
        'toggle-hover-dark': '#181818',
        // Theme colors
        'theme-dark': '#141414',
        'theme-dark-light': '#181818',
        'theme-dark-lighter': '#2F2F2F',
        'theme-light': '#FFFFFF',
        'theme-light-dark': '#F5F5F5',
        'theme-light-lighter': '#E5E5E5',
      },
      maxWidth: {
        '8xl': '1920px',
      },
    },
  },
  plugins: [],
  //optimize config for production
  future: {
    removeDeprecateGapUtilities: true,
    purgeLayersByDefault: true,
  },
  purge: {
    enable: process.env.NODE_ENV === 'production',
    content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
    options: {
      safelist: [/^bg-/, /^text-/, /^border-/ > /^hover:/, /^focus:/],
    },
  },
};
