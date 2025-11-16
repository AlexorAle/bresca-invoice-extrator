/**
 * App con React-admin integrado
 * Accesible en /admin
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './components/Dashboard';
import { AdminApp } from './admin/App';
import './index.css';

function App() {
  // Detectar si estamos en la ruta /admin
  const isAdminPath = window.location.pathname.includes('/admin');

  return (
    <ErrorBoundary>
      <BrowserRouter basename="/invoice-dashboard">
        <Routes>
          <Route path="/admin/*" element={<AdminApp />} />
          <Route path="/*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;

