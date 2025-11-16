/**
 * App principal - Punto de entrada
 * React-admin activado como framework principal
 */
import React from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import { AdminApp } from './admin/App';
import './index.css';

function App() {
  console.log('App component rendering with React-admin...');
  return (
    <ErrorBoundary>
      <AdminApp />
    </ErrorBoundary>
  );
}

export default App;
