import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// IMPORTANTE: base debe coincidir con la ruta en Traefik (/invoice-dashboard/)
// Traefik hace strip prefix, por lo que el contenedor recibe rutas sin el prefijo
// pero el navegador siempre solicita recursos con el prefijo completo
export default defineConfig({
  plugins: [react()],
  base: '/invoice-dashboard/', // Ruta absoluta que coincide con Traefik PathPrefix
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
