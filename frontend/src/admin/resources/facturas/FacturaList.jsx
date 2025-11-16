/**
 * Lista de Facturas - React-admin
 * Migrado desde FacturasTable.jsx
 */
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
import { Chip } from '@mui/material';
import { format } from 'date-fns';

/**
 * Filtros para la lista de facturas
 */
const FacturaFilter = (props) => (
  <Filter {...props}>
    <SearchInput source="proveedor" alwaysOn placeholder="Buscar por proveedor" />
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
      // Pasar month y year al dataProvider a través del filter
      // El dataProvider los leerá del filter
      sx={{
        '& .RaList-main': {
          backgroundColor: '#f8fafc',
        },
      }}
    >
      <Datagrid
        rowClick="show"
        sx={{
          '& .RaDatagrid-tableWrapper': {
            backgroundColor: '#ffffff',
            borderRadius: '20px',
            border: '1px solid #e2e8f0',
          },
          '& .RaDatagrid-headerCell': {
            fontSize: '1.25rem',
            fontWeight: 600,
            padding: '20px',
            textAlign: 'center',
            backgroundColor: '#f8fafc',
          },
          '& .RaDatagrid-rowCell': {
            fontSize: '1.125rem',
            padding: '20px',
          },
        }}
      >
        <TextField
          source="proveedor"
          label="Proveedor"
          sx={{ textAlign: 'left' }}
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
    </List>
  );
};

