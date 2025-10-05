/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './webapp/templates/**/*.html',
    './webapp/**/*.py'
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0b0e13',
        bg2: '#0a0c12',
        borderGlass: 'rgba(255,255,255,0.08)',
        card: 'rgba(255,255,255,0.05)',
        navy: '#0b1220',
        panel: '#0f162a',
        accent1: '#7c3aed',
        accent2: '#2563eb',
        accent3: '#06b6d4'
      },
      boxShadow: {
        glass: '0 10px 30px rgba(0,0,0,0.35)'
      },
      borderRadius: {
        'xl2': '14px'
      }
    },
  },
  plugins: [],
}
