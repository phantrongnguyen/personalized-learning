/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../../packages/shared/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff7fd',
          100: '#dbeeff',
          200: '#b8dcf5',
          300: '#85bfe8',
          400: '#3b91cc',
          500: '#0875bc',
          600: '#005a9c',
          700: '#004b82',
          800: '#073e68',
          900: '#0b3456',
          950: '#08233b',
        },
        slate: {
          750: '#29364b',
          850: '#151e2e',
          900: '#0f172a',
          950: '#090d16',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
