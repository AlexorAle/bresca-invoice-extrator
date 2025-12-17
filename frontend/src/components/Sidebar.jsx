import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FileText, Upload, ChevronLeft, Receipt, AlertCircle, Users } from 'lucide-react';

export function Sidebar({ activeSection, onSectionChange, onCollapseChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    if (onCollapseChange) {
      onCollapseChange(isCollapsed);
    }
  }, [isCollapsed, onCollapseChange]);

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'pendientes',
      label: 'Pendientes',
      icon: AlertCircle,
    },
    {
      id: 'reportes',
      label: 'Reportes',
      icon: FileText,
    },
    // {
    //   id: 'facturas',
    //   label: 'Facturas',
    //   icon: Receipt,
    // },
    {
      id: 'proveedores',
      label: 'Proveedores',
      icon: Users,
    },
    {
      id: 'datos',
      label: 'Datos',
      icon: Upload,
    },
  ];

  return (
    <div
      className={`h-screen fixed left-0 top-0 transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-16' : 'w-64'
      } z-50`}
      style={{
        backgroundColor: '#1e3a8a', // Fondo Base
        boxShadow: '2px 0 8px rgba(30, 58, 138, 0.1)', // Sombra Sidebar
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'rgba(224, 231, 255, 0.2)' }}>
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <Receipt size={24} style={{ color: '#e0e7ff' }} />
            <span className="font-semibold text-lg" style={{ color: '#e0e7ff' }}>Facturación</span>
          </div>
        )}
        {isCollapsed && (
          <div className="flex items-center justify-center w-full">
            <Receipt size={24} style={{ color: '#e0e7ff' }} />
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg transition-all duration-200"
            style={{ color: '#e0e7ff' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#1e40af'; // Hover
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          aria-label={isCollapsed ? 'Expandir sidebar' : 'Contraer sidebar'}
        >
          <ChevronLeft
            className={`transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`}
            size={20}
          />
        </button>
      </div>

      {/* Menu Items */}
      <nav className="p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isCollapsed ? 'justify-center' : ''
              }`}
              style={{
                backgroundColor: isActive ? '#2563eb' : 'transparent', // Activo: #2563eb
                color: '#e0e7ff', // Texto
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = '#1e40af'; // Hover
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
              title={isCollapsed ? item.label : ''}
            >
              <Icon size={20} className="flex-shrink-0" style={{ color: '#e0e7ff' }} />
              {!isCollapsed && (
                <span className="font-medium" style={{ color: '#e0e7ff' }}>{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

