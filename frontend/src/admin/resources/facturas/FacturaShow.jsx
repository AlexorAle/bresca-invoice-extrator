/**
 * Vista detallada de una Factura - React-admin
 */
import {
  Show,
  SimpleShowLayout,
  TextField,
  DateField,
  NumberField,
  FunctionField,
  useRecordContext,
} from 'react-admin';
import { Chip, Box, Typography, Divider } from '@mui/material';
import { format } from 'date-fns';

/**
 * Campo personalizado para formatear total
 */
const TotalField = () => {
  const record = useRecordContext();
  if (!record) return null;

  const total = parseFloat(record.total || 0);
  const formatted = new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(total);

  return (
    <Typography variant="h5" sx={{ fontWeight: 700, color: '#3b82f6' }}>
      {formatted}
    </Typography>
  );
};

/**
 * Campo personalizado para Estado
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
      size="medium"
      sx={{
        fontWeight: 600,
        fontSize: '1rem',
        padding: '8px 16px',
      }}
    />
  );
};

/**
 * Vista detallada de factura
 */
export const FacturaShow = (props) => (
  <Show {...props}>
    <SimpleShowLayout
      sx={{
        '& .RaSimpleShowLayout-root': {
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          padding: '24px',
        },
      }}
    >
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ mb: 2, fontWeight: 700 }}>
          Detalle de Factura
        </Typography>
        <Divider />
      </Box>

      <TextField source="proveedor" label="Proveedor" sx={{ fontSize: '1.125rem', mb: 2 }} />
      
      <FunctionField
        label="Fecha"
        render={(record) => {
          if (!record.fecha) return '-';
          try {
            const fecha = new Date(record.fecha);
            return format(fecha, 'dd/MM/yyyy');
          } catch (e) {
            return record.fecha;
          }
        }}
        sx={{ fontSize: '1.125rem', mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" sx={{ mb: 1, color: '#64748b' }}>
          Total
        </Typography>
        <TotalField />
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" sx={{ mb: 1, color: '#64748b' }}>
          Estado
        </Typography>
        <EstadoField />
      </Box>

      <FunctionField
        label="Categoría"
        render={(record) => record?.categoria || '-'}
        sx={{ fontSize: '1.125rem', mb: 2 }}
      />

      <FunctionField
        label="Razón"
        render={(record) => record?.razon || '-'}
        sx={{ fontSize: '1.125rem', mb: 2 }}
      />

      <FunctionField
        label="Nombre del archivo"
        render={(record) => record?.nombre || '-'}
        sx={{ fontSize: '1.125rem', mb: 2 }}
      />
    </SimpleShowLayout>
  </Show>
);

