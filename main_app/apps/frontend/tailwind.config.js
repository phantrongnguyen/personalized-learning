/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../../packages/shared/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          ...Object.fromEntries([50, 100, 200, 300, 400, 500, 600, 700].map(shade => [shade, "rgb(var(--color-brand-" + shade + ') / <alpha-value>)'])),
        },
        slate: {
          ...Object.fromEntries([50, 100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900, 950].map(shade => [shade, "rgb(var(--color-slate-" + shade + ') / <alpha-value>)'])),
        },
        foreground: 'rgb(var(--color-heading) / <alpha-value>)',
        'brand-tail': {
          400: 'rgb(var(--color-brand-tail-400) / <alpha-value>)',
          500: 'rgb(var(--color-brand-tail-500) / <alpha-value>)',
          600: 'rgb(var(--color-brand-tail-600) / <alpha-value>)',
        },
        ...Object.fromEntries(['emerald', 'rose', 'amber', 'blue', 'sky', 'cyan', 'teal', 'purple', 'orange', 'lime', 'green', 'yellow'].map(hue => [hue, Object.fromEntries([100, 200, 300, 400, 900, 950].map(shade => [shade, 'rgb(var(--color-' + hue + '-' + shade + ') / <alpha-value>)']))])),
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
