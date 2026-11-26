/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#180F43',
        'navy-light': '#2A2160',
        gold: '#C9A227',
        'gold-light': '#D5BB8B',
        bg: '#F7F6FB',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        urdu: ['"Noto Nastaliq Urdu"', 'serif'],
      },
    },
  },
  plugins: [],
}
