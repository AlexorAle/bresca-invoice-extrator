/**
 * Layout personalizado de React-admin
 * Integra el Sidebar custom del Dashboard original
 */
import React, { useState, useEffect } from 'react';
import { Layout as RALayout } from 'react-admin';
import { Sidebar } from '../components/Sidebar';

/**
 * Layout personalizado que usa el Sidebar custom
 */
export const Layout = (props) => {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Determinar sección activa desde la ruta de React-admin
  useEffect(() => {
    const updateActiveSection = () => {
      const path = window.location.pathname;
      if (path.includes('/facturas')) {
        setActiveSection('facturas');
      } else if (path.includes('/pendientes')) {
        setActiveSection('pendientes');
      } else if (path.includes('/carga-datos')) {
        setActiveSection('carga-datos');
      } else if (path === '/' || path === '') {
        setActiveSection('dashboard');
      } else {
        setActiveSection('dashboard');
      }
    };

    updateActiveSection();
    // Escuchar cambios en la ruta
    window.addEventListener('popstate', updateActiveSection);
    return () => window.removeEventListener('popstate', updateActiveSection);
  }, []);

  // Función para navegar usando el router de React-admin
  const handleSectionChange = (section) => {
    setActiveSection(section);
    // Navegar usando el router de React-admin (pushState para SPA)
    const basePath = window.location.pathname.split('/').slice(0, -1).join('/') || '';
    if (section === 'dashboard') {
      window.history.pushState({}, '', '/');
      window.dispatchEvent(new PopStateEvent('popstate'));
    } else if (section === 'pendientes') {
      window.history.pushState({}, '', '/pendientes');
      window.dispatchEvent(new PopStateEvent('popstate'));
    } else if (section === 'facturas') {
      window.history.pushState({}, '', '/facturas');
      window.dispatchEvent(new PopStateEvent('popstate'));
    } else if (section === 'carga-datos') {
      window.history.pushState({}, '', '/carga-datos');
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  return (
    <div className="min-h-screen bg-white flex" style={{ position: 'relative' }}>
      {/* Sidebar custom - Fixed */}
      <div style={{ position: 'fixed', left: 0, top: 0, zIndex: 1000 }}>
        <Sidebar 
          activeSection={activeSection} 
          onSectionChange={handleSectionChange}
          onCollapseChange={setIsSidebarCollapsed}
        />
      </div>

      {/* Main Content con margen para el sidebar */}
      <div 
        className="flex-1 transition-all duration-300" 
        style={{ 
          marginLeft: isSidebarCollapsed ? '64px' : '256px',
          minHeight: '100vh',
        }}
      >
        {/* Renderizar solo el contenido sin sidebar/appbar de React-admin */}
        {props.children}
      </div>
    </div>
  );
};

