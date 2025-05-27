module.exports = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    fontSize: {
      xs: '1rem',         // Increased from 0.875rem
      sm: '1.125rem',     // Increased from 1rem
      base: '1.25rem',    // Increased from 1.125rem
      lg: '1.375rem',     // Increased from 1.25rem
      xl: '1.5rem',       // Increased from 1.375rem
      '2xl': '1.75rem',   // Increased from 1.625rem
      '3xl': '2rem',      // Increased from 1.875rem
      '4xl': '2.75rem',   // Increased from 2.5rem
      '5xl': '3.5rem',    // Increased from 3.25rem
      '6xl': '4.5rem',    // Increased from 4.25rem
    },
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
      },
      animation: {
        'spin-slow': 'spin 2s linear infinite',
        'spin-fast': 'spin 0.5s linear infinite',
      }
    }
  },
  plugins: [],
}