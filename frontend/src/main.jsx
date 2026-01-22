import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'
import './index.css'
import App from './App.jsx'

// Client ID de Google OAuth
const GOOGLE_CLIENT_ID = '871033191224-40qifv1fp6ovn9kuk0b998e3ubl695ni.apps.googleusercontent.com'

// Script para forzar el margen izquierdo correcto después del render
// Sidebar expandido: 256px + 16px espacio = 272px
// Sidebar colapsado: 64px + 16px espacio = 80px
const forceMarginFix = () => {
  const fixMargin = () => {
    const mainContentDivs = document.querySelectorAll('div.flex-1.transition-all.duration-300');
    mainContentDivs.forEach(div => {
      const currentMargin = div.style.marginLeft;
      const marginValue = parseInt(currentMargin) || 0;
      
      // Detectar si el sidebar está colapsado (margen pequeño)
      const isCollapsed = marginValue < 150;
      
      if (isCollapsed) {
        // Sidebar colapsado: forzar 80px (64px sidebar + 16px espacio)
        if (marginValue !== 80) {
          div.style.setProperty('margin-left', '80px', 'important');
        }
      } else {
        // Sidebar expandido: forzar 272px (256px sidebar + 16px espacio)
        if (marginValue !== 272 && marginValue < 300) {
          div.style.setProperty('margin-left', '272px', 'important');
        }
      }
    });
  };
  
  // Ejecutar inmediatamente
  fixMargin();
  
  // Ejecutar después de que el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixMargin);
  }
  
  // Ejecutar después de un pequeño delay para asegurar que React haya renderizado
  setTimeout(fixMargin, 100);
  setTimeout(fixMargin, 500);
  
  // Observar cambios en el DOM
  const observer = new MutationObserver(fixMargin);
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style'] });
};

// Ejecutar el fix antes de renderizar
forceMarginFix();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <App />
    </GoogleOAuthProvider>
  </StrictMode>,
)

// Ejecutar el fix después del render también
setTimeout(forceMarginFix, 1000);
