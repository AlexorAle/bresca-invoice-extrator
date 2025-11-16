/**
 * AuthProvider simple para React-admin
 * Por ahora, sin autenticación real (todos los usuarios tienen acceso)
 */

export const authProvider = {
  login: async ({ username, password }) => {
    // Por ahora, siempre permite login
    localStorage.setItem('username', username);
    return Promise.resolve();
  },
  logout: () => {
    localStorage.removeItem('username');
    return Promise.resolve();
  },
  checkAuth: () => {
    // Por ahora, siempre autenticado
    return Promise.resolve();
  },
  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      localStorage.removeItem('username');
      return Promise.reject();
    }
    return Promise.resolve();
  },
  getPermissions: () => Promise.resolve(),
};

