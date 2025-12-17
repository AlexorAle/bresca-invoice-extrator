/**
 * Sidebar - Componente de sidebar migrado completamente a MUI
 * Reemplazo de Sidebar.jsx legacy (Tailwind)
 */
import React, { useState, useEffect } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import { LayoutDashboard, FileText, Upload, ChevronLeft, Receipt, AlertCircle, Users } from 'lucide-react';
import { COLORS, BORDER_RADIUS } from '../../admin/styles/designTokens';

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
      label: 'Facturas',
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

  const drawerWidth = isCollapsed ? 64 : 256;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#1e3a8a',
          borderRight: 'none',
          transition: 'width 0.3s ease',
          boxShadow: '2px 0 8px rgba(30, 58, 138, 0.1)',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          p: 2,
          borderBottom: '1px solid rgba(224, 231, 255, 0.2)',
          minHeight: '64px',
        }}
      >
        {!isCollapsed && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Receipt size={24} color="#e0e7ff" />
            <Typography
              sx={{
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontWeight: 600,
                fontSize: '18px',
                color: '#e0e7ff',
              }}
            >
              Facturación
            </Typography>
          </Box>
        )}
        {isCollapsed && (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
            <Receipt size={24} color="#e0e7ff" />
          </Box>
        )}
        <IconButton
          onClick={() => setIsCollapsed(!isCollapsed)}
          sx={{
            color: '#e0e7ff',
            '&:hover': {
              backgroundColor: '#1e40af',
            },
          }}
          aria-label={isCollapsed ? 'Expandir sidebar' : 'Contraer sidebar'}
        >
          <ChevronLeft
            size={20}
            style={{
              transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease',
            }}
          />
        </IconButton>
      </Box>

      {/* Menu Items */}
      <List sx={{ pt: 1 }}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <ListItem key={item.id} disablePadding sx={{ mb: 0.5, px: 1 }}>
              <ListItemButton
                onClick={() => onSectionChange(item.id)}
                sx={{
                  minHeight: '48px',
                  borderRadius: BORDER_RADIUS.md,
                  backgroundColor: isActive ? '#1e40af' : 'transparent',
                  color: '#e0e7ff',
                  '&:hover': {
                    backgroundColor: isActive ? '#1e40af' : 'rgba(30, 64, 175, 0.5)',
                  },
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  px: isCollapsed ? 1 : 2,
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: isCollapsed ? 0 : 40,
                    color: '#e0e7ff',
                    justifyContent: 'center',
                  }}
                >
                  <Icon size={20} />
                </ListItemIcon>
                {!isCollapsed && (
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{
                      fontFamily: "'Inter', 'Outfit', sans-serif",
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '15px',
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Drawer>
  );
}
