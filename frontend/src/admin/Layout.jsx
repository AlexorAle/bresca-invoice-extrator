/**
 * Layout personalizado de React-admin
 * Integra el Sidebar custom del Dashboard original
 */
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

/**
 * Layout personalizado que usa el Sidebar custom
 */
export const Layout = (props) => {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Determinar sección activa desde la ruta de React-admin
  useEffect(() => {
    const updateActiveSection = () => {
      const path = location.pathname;
      // Limpiar el path para obtener solo la parte del resource
      const cleanPath = path.replace(/\/invoice-dashboard\/?/, '').replace(/^\//, '');
      
      // if (cleanPath === 'facturas' || path.includes('/facturas')) {
      //   setActiveSection('facturas');
      // } else 
      if (cleanPath === 'proveedores' || path.includes('/proveedores')) {
        setActiveSection('proveedores');
      } else if (cleanPath === 'pendientes' || path.includes('/pendientes')) {
        setActiveSection('pendientes');
      } else if (cleanPath === 'reportes' || path.includes('/reportes')) {
        setActiveSection('reportes');
      } else if (cleanPath === 'datos' || path.includes('/datos')) {
        setActiveSection('datos');
      } else if (cleanPath === 'categorias' || path.includes('/categorias')) {
        setActiveSection('datos'); // Categorías está dentro de Datos
      } else if (cleanPath === 'dashboard' || cleanPath === '' || path.endsWith('/invoice-dashboard/') || path === '/') {
        setActiveSection('dashboard');
      } else {
        setActiveSection('dashboard');
      }
    };

    updateActiveSection();
  }, [location.pathname]);

  // Función para navegar usando el sistema de routing de React-admin
  const handleSectionChange = (section) => {
    setActiveSection(section);
    // Usar navigate de react-router (que React-admin usa internamente)
    if (section === 'dashboard') {
      // Dashboard es la ruta raíz en React-admin
      navigate('/');
    } else {
      navigate(`/${section}`);
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
        {/* Renderizar contenido de React-admin directamente */}
        {/* RALayout puede causar problemas, renderizar children directamente */}
        {props.children}
      </div>
    </div>
  );
};
