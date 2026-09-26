/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blue: {
          primary: '#0F62FE',
          hover: '#0353E9',
          light: '#EDF4FF',
        },
        gray: {
          900: '#161616',
          800: '#262626',
          700: '#393939',
          600: '#525252',
          500: '#6F6F6F',
          400: '#8D8D8D',
          300: '#A8A8A8',
          200: '#C6C6C6',
          100: '#E0E0E0',
          50: '#F4F4F4',
        },
        success: '#198038',
        warning: '#F1C21B',
        error: '#DA1E28',
        border: '#D0D0D0',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', '"Fira Code"', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
    },
  },
  plugins: [],
}
