import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FileText, Upload, ChevronLeft, Receipt, AlertCircle } from 'lucide-react';

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
    {
      id: 'carga-datos',
      label: 'Carga de Datos',
      icon: Upload,
    },
  ];

  return (
    <div
      className={`bg-gradient-to-b from-slate-900 to-slate-800 h-screen fixed left-0 top-0 transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-16' : 'w-64'
      } shadow-2xl z-50`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <Receipt className="text-white" size={24} />
            <span className="text-white font-semibold text-lg">Facturación</span>
          </div>
        )}
        {isCollapsed && (
          <div className="flex items-center justify-center w-full">
            <Receipt className="text-white" size={24} />
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-white hover:bg-slate-700 p-1.5 rounded-lg transition-colors"
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
                isActive
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'text-white hover:bg-slate-700'
              } ${isCollapsed ? 'justify-center' : ''}`}
              title={isCollapsed ? item.label : ''}
            >
              <Icon size={20} className="flex-shrink-0" />
              {!isCollapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

