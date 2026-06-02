/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../../packages/shared/src/**/*.{js,ts,jsx,tsx}",
    "../../packages/shared/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#edf9ef',
          100: '#d5efd9',
          200: '#aedfb7',
          300: '#79c98b',
          400: '#44aa5e',
          500: '#238b3d',
          600: '#156f30',
          700: '#0f5a28',
          800: '#0d4722',
          900: '#0b381d',
          950: '#051f0f',
        },
        secondary: {
          50: '#fff8e6',
          100: '#fff0bd',
          200: '#ffe17a',
          300: '#ffd139',
          400: '#efb90b',
          500: '#d6a000',
          600: '#ad7c00',
          700: '#8a5f05',
          800: '#704b09',
          900: '#5f3f0d',
        },
        earth: {
          50: '#fbf8ef',
          100: '#f3ead7',
          200: '#e5d3ad',
          300: '#d3b47d',
          400: '#bd914f',
          500: '#9a6d38',
          600: '#75512b',
          700: '#5c3f24',
          800: '#3f2c1b',
          900: '#2a1d13',
          950: '#160f0a',
        }
      },
      fontFamily: {
        sans: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Sora', 'Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 16px 50px rgba(23, 35, 28, 0.08)',
        card: '0 18px 45px rgba(24, 43, 33, 0.10)',
        glow: '0 18px 42px rgba(21, 111, 48, 0.24)',
      },
      borderRadius: {
        '2xl': '1.35rem',
        '3xl': '1.75rem',
      },
    },
  },
  plugins: [],
}
