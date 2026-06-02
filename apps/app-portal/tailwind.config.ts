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
          50: '#f0f8ed',
          100: '#d9efcf',
          200: '#b7dea3',
          300: '#8cc66d',
          400: '#66ab42',
          500: '#478f2a',
          600: '#34731f',
          700: '#285a1a',
          800: '#214818',
          900: '#1d3d17',
          950: '#0b2209',
        },
        secondary: {
          50: '#fff9e7',
          100: '#ffefbc',
          200: '#ffde78',
          300: '#ffc83a',
          400: '#f5ad0b',
          500: '#d99006',
          600: '#b86d08',
          700: '#94520d',
          800: '#794311',
          900: '#673813',
          950: '#3b1c05',
        },
        neutral: {
          50: '#fbfaf5',
          100: '#f4f0e5',
          200: '#e9dec9',
          300: '#d8c49c',
          400: '#c1a46d',
          500: '#ac8a4c',
          600: '#96733f',
          700: '#7d5b37',
          800: '#684c33',
          900: '#563f2d',
          950: '#2f2117',
        },
        // Semantic colors
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        // Legacy earth colors for compatibility
        earth: {
          50: '#fbfaf5',
          100: '#f4f0e5',
          200: '#e9dec9',
          300: '#d8c49c',
          400: '#9c8767',
          500: '#756348',
          600: '#5c4a35',
          700: '#473725',
          800: '#302417',
          900: '#1f170e',
        }
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        display: ['Sora', 'Manrope', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 12px 32px rgba(47, 33, 23, 0.08)',
        'medium': '0 18px 48px rgba(47, 33, 23, 0.12)',
        'strong': '0 30px 80px rgba(47, 33, 23, 0.18)',
        'glow': '0 18px 50px rgba(52, 115, 31, 0.22)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      }
    },
  },
  plugins: [],
}
