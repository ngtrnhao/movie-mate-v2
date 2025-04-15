const { version } = require('react');

module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {
      flexbox: true,
      grid: true,
      browser: ['> 1%', 'last 2  version', 'Firefox ESR'],
    },
  },
};
