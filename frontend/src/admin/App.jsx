/**
 * Componente principal de React-admin
 * Configuración completa del Admin con diseño original preservado
 */
import { Admin, Resource } from 'react-admin';
import { dataProvider } from './dataProvider';
import { authProvider } from './authProvider';
import { theme } from './theme';
import { Layout } from './Layout';
import { FacturaList } from './resources/facturas/FacturaList';
import { FacturaShow } from './resources/facturas/FacturaShow';
import { ReporteDashboard } from './resources/reportes/ReporteDashboard';
import { ReportePendientes } from './resources/reportes/ReportePendientes';
import { Reportes } from './resources/reportes/Reportes';
import { CargaDatosPanel } from './resources/carga-datos/CargaDatosPanel';
import { ProveedorList, ProveedorEdit } from './resources/proveedores';
import { CategoriasList, CategoriaCreate, CategoriaEdit } from './resources/categorias';
import { FileText, LayoutDashboard, AlertCircle, Upload, Tag } from 'lucide-react';

/**
 * Componente de icono personalizado para React-admin
 * Convierte iconos de lucide-react a formato compatible
 */
const createIcon = (LucideIcon) => {
  return (props) => <LucideIcon size={20} {...props} />;
};

/**
 * Componente Admin principal
 * IMPORTANTE: Traefik hace strip prefix, así que el contenedor recibe "/"
 * React-admin NO debe usar basename porque trabaja con rutas relativas desde "/"
 */
export const AdminApp = () => {
  return (
    <Admin
      dataProvider={dataProvider}
      authProvider={authProvider}
      theme={theme}
      layout={Layout}
      dashboard={ReporteDashboard}
      // NO usar basename - Traefik ya hace strip prefix
    >
      {/* Pendientes - Resource con list personalizado */}
      <Resource
        name="pendientes"
        list={ReportePendientes}
        options={{ label: 'Pendientes' }}
      />
      {/* Reportes - Resource con list personalizado */}
      <Resource
        name="reportes"
        list={Reportes}
        options={{ label: 'Reportes' }}
      />
      {/* Facturas - Resource estándar de React-admin - OCULTO TEMPORALMENTE */}
      {/* <Resource
        name="facturas"
        list={FacturaList}
        show={FacturaShow}
        options={{ label: 'Facturas' }}
      /> */}
      {/* Proveedores - Gestión de proveedores y categorías */}
      <Resource
        name="proveedores"
        list={ProveedorList}
        edit={ProveedorEdit}
        options={{ label: 'Proveedores' }}
      />
      {/* Datos - Resource con list personalizado */}
      <Resource
        name="datos"
        list={CargaDatosPanel}
        options={{ label: 'Datos' }}
      />
      {/* Categorías - Resource para gestión de categorías */}
      <Resource
        name="categorias"
        list={CategoriasList}
        create={CategoriaCreate}
        edit={CategoriaEdit}
        options={{ label: 'Categorías' }}
      />
    </Admin>
  );
};

