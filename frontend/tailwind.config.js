/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'ipad': '1024px',  // Custom breakpoint para iPad
        'lg': '1280px',    // Desktop real (cambiar de 1024px para evitar conflicto con ipad)
      },
      colors: {
        'primary': '#667eea',
        'primary-dark': '#764ba2',
      },
      boxShadow: {
        'card': '0 10px 30px rgba(0,0,0,0.08)',
        'card-hover': '0 20px 40px rgba(0,0,0,0.12)',
        'header': '0 20px 60px rgba(0,0,0,0.1)',
        'button-active': '0 4px 12px rgba(102, 126, 234, 0.4)',
      }
    },
  },
  plugins: [],
}

