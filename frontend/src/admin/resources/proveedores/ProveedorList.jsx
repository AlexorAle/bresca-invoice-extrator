/**
 * Lista de Proveedores con filtro alfabético
 * Mantiene el mismo estilo del dashboard
 */
import React, { useState, useEffect } from 'react';
import {
  List,
  Datagrid,
  TextField,
  NumberField,
  EditButton,
  useListContext,
  TopToolbar,
  SearchInput,
  SelectInput,
  Filter,
  FunctionField,
  useRecordContext,
  Edit,
  SimpleForm,
  TextInput,
  required,
  useUpdate,
  useNotify,
  useRefresh,
  useGetList,
} from 'react-admin';
import { Box, Button, Typography, Chip, Menu, MenuItem, CircularProgress, TextField as MuiTextField } from '@mui/material';
import { SPACING, PAGE_LAYOUT, INPUT_STYLES, TABLE_STYLES, BUTTON_HEIGHTS, BORDER_RADIUS } from '../../styles/designTokens';
import { 
  ShoppingCart, 
  Coffee, 
  Apple, 
  Wrench, 
  Zap, 
  Phone, 
  Briefcase, 
  Sparkles, 
  Settings, 
  Truck, 
  MoreHorizontal,
  Utensils,
  Fish,
  Carrot,
  Milk,
  Wine,
  Droplet,
  Croissant,
  Store,
  Package,
  Hammer,
  Droplets,
  Smartphone,
  Laptop,
  ShoppingBag,
  Megaphone,
  Shirt,
  Crown,
  CreditCard,
  Shield,
  GraduationCap
} from 'lucide-react';
import { CategoriaSelectInput } from './CategoriaSelectInput';

// Mapeo de iconos por nombre de categoría (para mantener compatibilidad visual)
const ICON_MAP = {
  'Carnes y Pescados': Fish,
  'Frutas y Verduras': Carrot,
  'Lácteos y Huevos': Milk,
  'Bebidas Alcohólicas': Wine,
  'Bebidas No Alcohólicas': Droplet,
  'Panadería': Croissant,
  'Cash & Carry / Supermercado': Store,
  'Menaje y Desechables': Package,
  'Limpieza e Higiene': Sparkles,
  'Mantenimiento y Reparaciones': Hammer,
  'Energía y Agua': Droplets,
  'Telecomunicaciones': Smartphone,
  'Software y Tecnología': Laptop,
  'Delivery y Plataformas': ShoppingBag,
  'Marketing y Publicidad': Megaphone,
  'Uniformes': Shirt,
  'Franquicia / Royalties': Crown,
  'Banca y Financieros': CreditCard,
  'Seguros y Asesorías': Shield,
  'Formación': GraduationCap,
  'Otros': MoreHorizontal,
};

// Mapeo de colores por nombre de categoría
const COLOR_MAP = {
  'Carnes y Pescados': '#EF4444',
  'Frutas y Verduras': '#10B981',
  'Lácteos y Huevos': '#FBBF24',
  'Bebidas Alcohólicas': '#7C3AED',
  'Bebidas No Alcohólicas': '#3B82F6',
  'Panadería': '#F59E0B',
  'Cash & Carry / Supermercado': '#10B981',
  'Menaje y Desechables': '#6366F1',
  'Limpieza e Higiene': '#14B8A6',
  'Mantenimiento y Reparaciones': '#F97316',
  'Energía y Agua': '#06B6D4',
  'Telecomunicaciones': '#3B82F6',
  'Software y Tecnología': '#8B5CF6',
  'Delivery y Plataformas': '#EC4899',
  'Marketing y Publicidad': '#F59E0B',
  'Uniformes': '#6366F1',
  'Franquicia / Royalties': '#FBBF24',
  'Banca y Financieros': '#10B981',
  'Seguros y Asesorías': '#3B82F6',
  'Formación': '#8B5CF6',
  'Otros': '#6B7280',
};

// Hook para cargar categorías desde la BD
const useCategorias = () => {
  const { data, isLoading, error } = useGetList('categorias', {
    pagination: { page: 1, perPage: 500 },
    sort: { field: 'nombre', order: 'ASC' },
    filter: { activo: true },
  });

  // Mapear categorías y eliminar duplicados por nombre
  const categoriasMap = new Map();
  data?.forEach(cat => {
    // Usar nombre como clave para evitar duplicados
    if (!categoriasMap.has(cat.nombre)) {
      categoriasMap.set(cat.nombre, {
        id: cat.nombre, // Usar nombre como ID para compatibilidad
        name: cat.nombre,
        icon: ICON_MAP[cat.nombre] || MoreHorizontal,
        color: (cat.color && cat.color !== 'null' && cat.color !== null) ? cat.color : (COLOR_MAP[cat.nombre] || '#6B7280'), // Usar color de BD, fallback a mapa
      });
    }
  });
  
  const categorias = Array.from(categoriasMap.values());

  return { categorias, isLoading, error };
};

/**
 * Filtro alfabético - Componente de letras
 */
const AlphabetFilter = () => {
  const { setFilters, filterValues } = useListContext();
  const alfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const [selectedLetter, setSelectedLetter] = useState(null);

  useEffect(() => {
    if (filterValues && filterValues.letra) {
      setSelectedLetter(filterValues.letra);
    }
  }, [filterValues]);

  const handleLetterClick = (letter) => {
    if (selectedLetter === letter) {
      // Si ya está seleccionada, quitar filtro
      setSelectedLetter(null);
      setFilters({ ...filterValues, letra: undefined }, filterValues);
    } else {
      // Aplicar filtro
      setSelectedLetter(letter);
      setFilters({ ...filterValues, letra: letter }, filterValues);
    }
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography 
        variant="body2" 
        sx={{ 
          mb: 1.5, 
          color: '#64748b',
          fontWeight: 500,
          fontFamily: "'Inter', 'Outfit', sans-serif",
          textTransform: 'uppercase',
          fontSize: '0.875rem',
          letterSpacing: '0.5px',
        }}
      >
        FILTRAR POR LETRA:
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {alfabeto.map((letter) => (
          <Button
            key={letter}
            onClick={() => handleLetterClick(letter)}
            sx={{
              minWidth: '40px',
              width: '40px',
              height: '40px',
              padding: 0,
              backgroundColor: selectedLetter === letter ? '#2563eb' : '#ffffff',
              color: selectedLetter === letter ? '#ffffff' : '#1e293b',
              border: selectedLetter === letter ? 'none' : '1px solid #e5e7eb',
              borderRadius: '50%',
              fontFamily: "'Inter', 'Outfit', sans-serif",
              fontSize: '0.875rem',
              fontWeight: selectedLetter === letter ? 600 : 500,
              '&:hover': {
                backgroundColor: selectedLetter === letter ? '#1e40af' : '#f8fafc',
                borderColor: selectedLetter === letter ? 'none' : '#cbd5e1',
              },
              transition: 'all 0.2s ease',
            }}
          >
            {letter}
          </Button>
        ))}
      </Box>
    </Box>
  );
};

/**
 * Buscador personalizado (no usa el sistema de filtros de React-admin)
 */
const CustomSearchInput = () => {
  const { setFilters, filterValues } = useListContext();
  const [searchValue, setSearchValue] = React.useState(filterValues?.search || '');

  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchValue(value);
    setFilters({ ...filterValues, search: value || undefined }, filterValues);
  };

  return (
    <MuiTextField
      placeholder="Buscar proveedor"
      value={searchValue}
      onChange={handleSearchChange}
      size="small"
      sx={{
        width: INPUT_STYLES.width,
        '& .MuiOutlinedInput-root': {
          height: INPUT_STYLES.height,
          borderRadius: INPUT_STYLES.borderRadius,
          '& fieldset': {
            borderColor: '#d1d5db',
          },
          '&:hover fieldset': {
            borderColor: '#9ca3af',
          },
          '&.Mui-focused fieldset': {
            borderColor: '#3b82f6',
            boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
          },
        },
      }}
    />
  );
};

/**
 * Campo personalizado para mostrar y editar categoría (edición inline)
 */
const CategoriaField = ({ sx = {} }) => {
  const record = useRecordContext();
  const [update, { isLoading }] = useUpdate();
  const notify = useNotify();
  const refresh = useRefresh();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const { categorias } = useCategorias();

  // Encontrar la categoría actual con su icono y color
  const categoriaActual = categorias.find(cat => cat.id === record?.categoria) || null;
  const colorActual = categoriaActual?.color || '#6B7280';
  const IconActual = categoriaActual?.icon || MoreHorizontal;

  const handleClick = (event) => {
    event.stopPropagation(); // Evitar que se abra el formulario de edición completo
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSelectCategoria = async (categoriaId) => {
    try {
      await update(
        'proveedores',
        {
          id: record.id,
          data: { categoria: categoriaId },
          previousData: record,
        },
        {
          onSuccess: () => {
            notify('Categoría actualizada correctamente', { type: 'success' });
            refresh();
            handleClose();
          },
          onError: (error) => {
            notify('Error al actualizar categoría', { type: 'error' });
            console.error('Error updating categoria:', error);
          },
        }
      );
    } catch (error) {
      notify('Error al actualizar categoría', { type: 'error' });
      console.error('Error updating categoria:', error);
    }
  };

  if (!record) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', ...sx }}>
      {isLoading ? (
        <CircularProgress size={20} />
      ) : (
        <>
          <Chip
            label={record.categoria || 'Sin Categoría'}
            icon={<IconActual size={14} />}
            size="small"
            onClick={handleClick}
            sx={{
              backgroundColor: record.categoria ? colorActual : '#E5E7EB',
              color: record.categoria ? 'white' : '#6B7280',
              fontWeight: 600,
              fontSize: '0.75rem',
              cursor: 'pointer',
              '&:hover': {
                opacity: 0.8,
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease',
            }}
          />
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleClose}
            onClick={(e) => e.stopPropagation()}
            PaperProps={{
              sx: {
                mt: 1,
                minWidth: 200,
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              },
            }}
          >
            {categorias.map((categoria) => {
              const Icon = categoria.icon;
              const isSelected = record.categoria === categoria.id;
              
              return (
                <MenuItem
                  key={categoria.id}
                  onClick={() => handleSelectCategoria(categoria.id)}
                  selected={isSelected}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    py: 1.5,
                    px: 2,
                    '&:hover': {
                      backgroundColor: '#f1f5f9',
                    },
                    '&.Mui-selected': {
                      backgroundColor: `${categoria.color}15`,
                      '&:hover': {
                        backgroundColor: `${categoria.color}25`,
                      },
                    },
                  }}
                >
                  <Icon size={18} color={categoria.color} />
                  <Typography
                    sx={{
                      fontFamily: "'Inter', 'Outfit', sans-serif",
                      fontWeight: isSelected ? 600 : 500,
                      color: isSelected ? categoria.color : '#1e293b',
                    }}
                  >
                    {categoria.name}
                  </Typography>
                  {isSelected && (
                    <Box
                      sx={{
                        ml: 'auto',
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: categoria.color,
                      }}
                    />
                  )}
                </MenuItem>
              );
            })}
          </Menu>
        </>
      )}
    </Box>
  );
};

/**
 * Campo personalizado para el total de importe
 */
const ImporteTotalField = () => {
  const record = useRecordContext();
  if (!record) return null;

  const importe = record.total_importe || 0;
  const formatted = new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
  }).format(importe);

  return (
    <Typography
      variant="body2"
      sx={{
        fontWeight: 600,
        color: importe > 0 ? '#10b981' : '#94a3b8',
        fontFamily: "'Inter', 'Outfit', sans-serif",
        fontSize: '0.9375rem',
      }}
    >
      {formatted}
    </Typography>
  );
};

/**
 * Actions personalizadas
 */
const ListActions = () => (
  <TopToolbar>
    {/* Aquí puedes agregar botones adicionales si es necesario */}
  </TopToolbar>
);

/**
 * Lista principal de proveedores
 */
export const ProveedorList = (props) => (
  <List
    {...props}
    filters={false}
    actions={<ListActions />}
    perPage={50}
    sort={{ field: 'nombre', order: 'ASC' }}
    empty={false}
    sx={{
      '& .RaList-main': {
        backgroundColor: '#f8fafc',
        paddingTop: 0,
      },
      '& .RaList-content': {
        boxShadow: 'none',
        borderTop: 'none',
      },
      '& .RaList-actions': {
        display: 'none',
      },
    }}
  >
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#f8fafc',
        padding: 0,
        margin: 0,
      }}
    >
      <div className="p-2 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
          {/* Título - PRIORIDAD 1: margin-top: 48px */}
          <Box sx={{ mt: PAGE_LAYOUT.titleMarginTop, mb: PAGE_LAYOUT.titleMarginBottom }}>
            <Typography
              variant="h3"
              sx={{
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontWeight: 700,
                fontSize: '2rem',
                color: '#1e293b',
                margin: 0,
              }}
            >
              Gestión de Proveedores
            </Typography>
          </Box>

          {/* Filtro A-Z */}
          <Box sx={{ mb: SPACING.md }}>
            <AlphabetFilter />
          </Box>

          {/* Buscador debajo del filtro alfabético */}
          <Box sx={{ mb: SPACING.md }}>
            <CustomSearchInput />
          </Box>

          {/* Tabla de proveedores */}
          <Datagrid
            rowClick={false}
            bulkActionButtons={false}
            sx={{
              '& .RaDatagrid-tableWrapper': {
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                border: '1px solid #e2e8f0',
                overflow: 'hidden',
              },
              '& .RaDatagrid-headerCell': {
                height: TABLE_STYLES.headerHeight,
                fontSize: TABLE_STYLES.headerFontSize,
                fontWeight: 600,
                padding: `0 ${TABLE_STYLES.cellPaddingHorizontal}`,
                textAlign: 'center',
                backgroundColor: '#f9fafb',
                color: '#475569',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontFamily: "'Inter', 'Outfit', sans-serif",
              },
              '& .RaDatagrid-row': {
                height: TABLE_STYLES.rowHeight,
              },
              '& .RaDatagrid-rowCell': {
                height: TABLE_STYLES.rowHeight,
                fontSize: TABLE_STYLES.cellFontSize,
                padding: `${TABLE_STYLES.cellPaddingVertical} ${TABLE_STYLES.cellPaddingHorizontal}`,
                fontFamily: "'Inter', 'Outfit', sans-serif",
                textAlign: 'center',
                verticalAlign: 'middle',
                borderBottom: '1px solid #e5e7eb',
              },
              '& .RaDatagrid-row:hover': {
                backgroundColor: '#f8fafc',
              },
            }}
          >
            <TextField 
              source="nombre" 
              label="Proveedor"
              sx={{ 
                fontWeight: 500,
                textAlign: 'center',
                '& .RaTextField-root': {
                  textAlign: 'center',
                },
              }}
            />
            <CategoriaField 
              label="Categoría"
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            />
            <NumberField 
              source="total_facturas" 
              label="Facturas"
              sx={{ 
                textAlign: 'center',
                fontWeight: 600,
              }}
            />
            <FunctionField
              label="Total Facturado"
              render={(record) => (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <ImporteTotalField />
                </Box>
              )}
            />
            <TextField 
              source="nif_cif" 
              label="NIF/CIF"
              emptyText="-"
              sx={{ 
                textAlign: 'center',
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontSize: '0.9375rem',
              }}
            />
            <EditButton 
              label="Editar"
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: BUTTON_HEIGHTS.secondary,
                padding: `0 ${SPACING.md}`,
                borderRadius: BORDER_RADIUS.md,
                fontSize: '14px',
                fontWeight: 400,
                color: '#2563eb',
                '&:hover': {
                  backgroundColor: '#dbeafe',
                },
              }}
            />
          </Datagrid>
        </div>
      </div>
    </Box>
  </List>
);

/**
 * Formulario de edición de proveedor
 */
export const ProveedorEdit = () => (
  <Edit
    sx={{
      '& .RaEdit-main': {
        backgroundColor: '#f8fafc',
      },
    }}
  >
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#f8fafc',
        padding: 0,
        margin: 0,
      }}
    >
      <div className="p-2 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6" style={{ maxWidth: '800px' }}>
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h3"
              sx={{
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontWeight: 700,
                fontSize: '2rem',
                color: '#1e293b',
              }}
            >
              Editar Proveedor
            </Typography>
          </Box>

          {/* Formulario */}
          <Box
            sx={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              padding: '32px',
            }}
          >
            <SimpleForm
              sx={{
                '& .MuiTextField-root': {
                  mb: 3,
                },
                '& .MuiFormControl-root': {
                  mb: 3,
                },
              }}
            >
              <TextInput 
                source="nombre" 
                label="Nombre del Proveedor" 
                disabled 
                fullWidth
                sx={{
                  '& .MuiInputBase-root': {
                    backgroundColor: '#f8fafc',
                  },
                }}
              />
              <CategoriaSelectInput />
              <TextInput 
                source="nif_cif" 
                label="NIF/CIF" 
                fullWidth
                placeholder="Ej: B12345678"
              />
              <TextInput 
                source="email_contacto" 
                label="Email de Contacto" 
                type="email" 
                fullWidth
                placeholder="contacto@proveedor.com"
              />
            </SimpleForm>
          </Box>
        </div>
      </div>
    </Box>
  </Edit>
);
