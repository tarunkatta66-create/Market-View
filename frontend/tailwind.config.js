/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bgDark: '#0B0F17',
        cardDark: '#0F172A',
        borderDark: '#1E293B',
        upGreen: '#10B981',
        downRed: '#EF4444',
        accentAmber: '#F59E0B',
        accentTeal: '#14B8A6'
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace']
      }
    },
  },
  plugins: [],
}
