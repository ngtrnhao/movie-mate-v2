// .eslintrc.js
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'plugin:tailwindcss/recommended',
    'prettier',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react', 'tailwindcss', 'prettier'],
  rules: {
    'prettier/prettier': [
      'error',
      {
        endOfLine: 'auto',
        singleQuote: true,
      },
    ],
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
    'tailwindcss/classnames-order': 'warn',
    'tailwindcss/no-custom-classname': [
      'warn',
      {
        whitelist: [
          'text-toggle-light',
          'text-toggle-dark',
          'bg-toggle-hover-light',
          'bg-toggle-hover-dark',
          'hover:bg-toggle-hover-light',
          'hover:bg-toggle-hover-dark',
          'dark:text-toggle-dark',
          'dark:hover:bg-toggle-hover-dark',
        ],
      },
    ],
    'tailwindcss/no-contradicting-classname': 'error',
  },
  settings: {
    react: {
      version: 'detect',
    },
    tailwindcss: {
      // Đường dẫn tới file config của Tailwind
      config: './tailwind.config.js',
    },
  },
};
