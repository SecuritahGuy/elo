/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nfl: {
          primary: '#013369',
          secondary: '#D50A0A',
          accent: '#FFB612',
          dark: '#1a1a1a',
          light: '#f8f9fa'
        }
      },
      fontFamily: {
        'nfl': ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
