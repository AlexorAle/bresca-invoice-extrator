/**
 * AuthProvider para React-admin
 * Integrado con autenticación Google OAuth
 * Verifica sesión con el backend en cada petición
 */

export const authProvider = {
  login: async ({ username, password }) => {
    // Este método no se usa con Google OAuth
    // El login se maneja en LoginPage.jsx
    return Promise.resolve();
  },
  
  logout: async () => {
    try {
      await fetch('/invoice-api/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    }
    // Recargar página para limpiar estado
    window.location.href = '/invoice-dashboard/';
    return Promise.resolve();
  },
  
  checkAuth: async () => {
    try {
      const response = await fetch('/invoice-api/api/auth/me', {
        method: 'GET',
        credentials: 'include',
      });
      
      if (!response.ok) {
        // Si no hay sesión, rechazar para que React-admin redirija
        return Promise.reject();
      }
      
      return Promise.resolve();
    } catch (error) {
      console.error('Error al verificar autenticación:', error);
      return Promise.reject();
    }
  },
  
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      // Si hay error de autenticación, redirigir a login
      window.location.href = '/invoice-dashboard/';
      return Promise.reject();
    }
    return Promise.resolve();
  },
  
  getPermissions: () => Promise.resolve(),
};

