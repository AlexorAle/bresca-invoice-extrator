/**
 * Lista de Facturas - React-admin
 * Migrado desde FacturasTable.jsx
 */
import React from 'react';
import {
  List,
  Datagrid,
  TextField,
  DateField,
  NumberField,
  FunctionField,
  Filter,
  SearchInput,
  SelectInput,
  DateInput,
  NumberInput,
  useRecordContext,
} from 'react-admin';
import { Chip, Box, Typography, TextField as MuiTextField } from '@mui/material';
import { format } from 'date-fns';
import { SPACING, PAGE_LAYOUT, INPUT_STYLES, TABLE_STYLES, BORDER_RADIUS } from '../../styles/designTokens';
import { useListContext } from 'react-admin';

/**
 * Buscador personalizado (debajo del título)
 */
const CustomSearchInput = () => {
  const { setFilters, filterValues } = useListContext();
  const [searchValue, setSearchValue] = React.useState(filterValues?.proveedor || '');

  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchValue(value);
    setFilters({ ...filterValues, proveedor: value || undefined }, filterValues);
  };

  return (
    <MuiTextField
      placeholder="Buscar por proveedor"
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
 * Filtros adicionales (ocultos por defecto, se pueden mostrar con un botón)
 */
const FacturaFilter = (props) => (
  <Filter {...props}>
    <SelectInput
      source="estado"
      choices={[
        { id: 'procesada', name: 'Procesada' },
        { id: 'pendiente', name: 'Pendiente' },
      ]}
      placeholder="Filtrar por estado"
    />
    <DateInput source="fecha_gte" label="Fecha desde" />
    <DateInput source="fecha_lte" label="Fecha hasta" />
    <NumberInput source="total_gte" label="Total desde" />
    <NumberInput source="total_lte" label="Total hasta" />
  </Filter>
);

/**
 * Campo personalizado para Estado con chip de color
 */
const EstadoField = () => {
  const record = useRecordContext();
  if (!record) return null;

  const estado = record.estado || 'pendiente';
  const color = estado === 'procesada' ? 'success' : 'warning';
  const label = estado === 'procesada' ? 'Procesada' : 'Pendiente';

  return (
    <Chip
      label={label}
      color={color}
      size="small"
      sx={{
        fontWeight: 600,
        fontSize: '0.875rem',
      }}
    />
  );
};

/**
 * Campo personalizado para formatear fecha
 */
const FechaField = (props) => {
  const record = useRecordContext();
  if (!record || !record.fecha) return null;

  try {
    const fecha = new Date(record.fecha);
    const formatted = format(fecha, 'dd/MM/yyyy');
    return <span>{formatted}</span>;
  } catch (e) {
    return <span>{record.fecha}</span>;
  }
};

/**
 * Campo personalizado para formatear total
 */
const TotalField = (props) => {
  const record = useRecordContext();
  if (!record) return null;

  const total = parseFloat(record.total || 0);
  const formatted = new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(total);

  return <span style={{ fontWeight: 600 }}>{formatted}</span>;
};

/**
 * Lista principal de facturas
 */
export const FacturaList = (props) => {
  // Obtener mes y año del filtro o usar valores por defecto
  const currentDate = new Date();
  const defaultMonth = currentDate.getMonth() + 1;
  const defaultYear = currentDate.getFullYear();

  return (
    <List
      {...props}
      filters={<FacturaFilter />}
      perPage={25}
      sort={{ field: 'fecha', order: 'DESC' }}
      filterDefaultValues={{
        month: defaultMonth,
        year: defaultYear,
      }}
      empty={false}
      sx={{
        '& .RaList-main': {
          backgroundColor: '#f8fafc',
        },
        '& .RaList-content': {
          boxShadow: 'none',
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
                Facturas
              </Typography>
            </Box>

            {/* Buscador - PRIORIDAD 1: debajo del título, alineado a la derecha */}
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              mb: SPACING.md,
            }}>
              <CustomSearchInput />
            </Box>

            {/* Tabla de facturas */}
            <Datagrid
              rowClick="show"
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
                  textAlign: 'left',
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
                  borderBottom: '1px solid #e5e7eb',
                },
                '& .RaDatagrid-row:hover': {
                  backgroundColor: '#f8fafc',
                },
              }}
            >
              <TextField
                source="proveedor"
                label="Proveedor"
                sx={{ fontWeight: 500 }}
              />
              <FechaField
                source="fecha"
                label="Fecha"
                sx={{ textAlign: 'center' }}
              />
              <TotalField
                source="total"
                label="Total"
                sx={{ textAlign: 'center' }}
              />
              <EstadoField
                source="estado"
                label="Estado"
                sx={{ textAlign: 'center' }}
              />
            </Datagrid>
          </div>
        </div>
      </Box>
    </List>
  );
};

