/**
 * App principal - Punto de entrada
 * React-admin activado como framework principal
 * Con protección de autenticación Google
 */
import React from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import { AdminApp } from './admin/App';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './components/LoginPage';
import './index.css';

function AppContent() {
  const { isAuthenticated, loading, handleLoginSuccess } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <div>Cargando...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return <AdminApp />;
}

function App() {
  console.log('App component rendering with React-admin...');
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
