/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'torn-bg': '#0a0a0f',
        'torn-surface': '#111118',
        'torn-card': '#16161f',
        'torn-border': '#2a2a3a',
        'torn-muted': '#3a3a50',
        'neon-green': '#00ff88',
        'neon-gold': '#ffd700',
        'neon-red': '#ff3366',
        'neon-blue': '#00aaff',
        'text-primary': '#e8e8f0',
        'text-secondary': '#8888a8',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'neon-green': '0 0 8px rgba(0,255,136,0.4), 0 0 20px rgba(0,255,136,0.15)',
        'neon-gold': '0 0 8px rgba(255,215,0,0.4), 0 0 20px rgba(255,215,0,0.15)',
        'neon-red': '0 0 8px rgba(255,51,102,0.4), 0 0 20px rgba(255,51,102,0.15)',
        'card': '0 4px 24px rgba(0,0,0,0.6)',
      },
      animation: {
        'pulse-green': 'pulse-green 2s infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
      },
      keyframes: {
        'pulse-green': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

