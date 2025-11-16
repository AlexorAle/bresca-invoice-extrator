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
import { CargaDatosPanel } from './resources/carga-datos/CargaDatosPanel';
import { FileText, LayoutDashboard, AlertCircle, Upload } from 'lucide-react';

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
      <Resource
        name=""
        list={ReporteDashboard}
        options={{ label: 'Dashboard' }}
      />
      <Resource
        name="pendientes"
        list={ReportePendientes}
        options={{ label: 'Pendientes' }}
      />
      <Resource
        name="facturas"
        list={FacturaList}
        show={FacturaShow}
        options={{ label: 'Facturas' }}
      />
      <Resource
        name="carga-datos"
        list={CargaDatosPanel}
        options={{ label: 'Carga de Datos' }}
      />
    </Admin>
  );
};

