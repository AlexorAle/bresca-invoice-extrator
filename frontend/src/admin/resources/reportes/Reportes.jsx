/**
 * Página de Reportes - React-admin
 * Vista modular con tarjetas de diferentes reportes
 */
import React, { useState, useMemo } from 'react';
import { Box, Typography, Card, CardContent, CardHeader } from '@mui/material';
import { BarChart3, Users, TrendingUp, Calendar, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useInvoiceData } from '../../../hooks/useInvoiceData';
import { MONTH_NAMES } from '../../../utils/constants';

/**
 * Tarjeta de reporte individual
 */
const ReportCard = ({ title, icon: Icon, color, children, yearSelector }) => {
  const colorMap = {
    purple: {
      bg: '#9333ea', // purple-600
      light: '#e9d5ff', // purple-200
      text: '#ffffff',
    },
    blue: {
      bg: '#3b82f6', // blue-500
      light: '#dbeafe', // blue-100
      text: '#ffffff',
    },
    green: {
      bg: '#10b981', // green-500
      light: '#d1fae5', // green-100
      text: '#ffffff',
    },
  };

  const colors = colorMap[color] || colorMap.blue;

  return (
    <Card
      sx={{
        borderRadius: '16px',
        border: '1px solid #e5e7eb',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardHeader
        sx={{
          backgroundColor: colors.bg,
          color: colors.text,
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          minHeight: '72px',
          '& .MuiCardHeader-content': {
            overflow: 'visible',
            flex: '1 1 auto',
            minWidth: 0,
          },
          '& .MuiCardHeader-action': {
            flex: '0 0 auto',
            marginLeft: '16px',
          },
        }}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1, minWidth: 0 }}>
            <Icon size={28} color={colors.text} />
            <Typography
              variant="h5"
              component="span"
              sx={{
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontWeight: 700,
                fontSize: '1.5rem',
                color: colors.text,
                lineHeight: 1.2,
                flex: '0 0 auto',
              }}
            >
              {title}
            </Typography>
          </Box>
        }
        action={
          yearSelector ? (
            <Box sx={{ ml: 2, zIndex: 1000 }}>
              {yearSelector}
            </Box>
          ) : null
        }
      />
      <CardContent
        sx={{
          padding: '20px',
          flex: 1,
          backgroundColor: '#ffffff',
        }}
      >
        {children}
      </CardContent>
    </Card>
  );
};

/**
 * Selector de Año - Similar al del Header pero solo para año
 * Asegurar que sea visible y funcional
 */
const YearSelector = ({ selectedYear, onYearChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = React.useRef(null);

  // Cerrar dropdown al hacer click fuera
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleYearChange = (increment) => {
    onYearChange(selectedYear + increment);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef} style={{ zIndex: 1000 }}>
      <div 
        className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg shadow-lg overflow-hidden cursor-pointer w-32 border border-slate-700 transition-all hover:shadow-blue-500/10 hover:shadow-xl hover:scale-105"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        style={{ position: 'relative', zIndex: 1001 }}
      >
        <div className="px-3 py-2 flex items-center justify-between border-b border-slate-700">
          <Calendar className="text-blue-400" size={14} />
          <ChevronDown 
            className={`text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
            size={12} 
          />
        </div>
        <div className="px-3 py-2 text-center">
          <div className="text-base font-bold text-blue-400">
            {selectedYear}
          </div>
        </div>
        <div className="h-0.5 bg-gradient-to-r from-blue-500 via-blue-400 to-blue-500"></div>
      </div>

      {isOpen && (
        <div 
          className="absolute top-full mt-2 right-0 bg-slate-900 rounded-lg shadow-2xl overflow-hidden border border-slate-700 w-40 animate-[fadeIn_0.3s_ease-out]"
          style={{ zIndex: 1002 }}
        >
          <div className="bg-slate-800 px-4 py-3 flex items-center justify-between border-b border-slate-700">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleYearChange(-1);
              }}
              className="p-1.5 hover:bg-slate-700 rounded transition-all text-white hover:scale-110"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-sm font-semibold text-white">{selectedYear}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleYearChange(1);
              }}
              className="p-1.5 hover:bg-slate-700 rounded transition-all text-white hover:scale-110"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Selector de Mes y Año - Para Top Proveedores
 */
const MonthYearSelector = ({ selectedMonth, selectedYear, onMonthChange, onYearChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = React.useRef(null);

  const months = MONTH_NAMES;

  // Cerrar dropdown al hacer click fuera
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleMonthSelect = (monthIndex) => {
    onMonthChange(monthIndex);
    setIsOpen(false);
  };

  const handleYearChange = (increment) => {
    onYearChange(selectedYear + increment);
  };

  return (
    <div className="relative" ref={dropdownRef} style={{ zIndex: 1000 }}>
      <div 
        className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg shadow-lg overflow-hidden cursor-pointer w-40 border border-slate-700 transition-all hover:shadow-blue-500/10 hover:shadow-xl hover:scale-105"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        style={{ position: 'relative', zIndex: 1001 }}
      >
        <div className="px-3 py-2 flex items-center justify-between border-b border-slate-700">
          <Calendar className="text-blue-400" size={14} />
          <ChevronDown 
            className={`text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
            size={12} 
          />
        </div>
        <div className="px-3 py-2 text-center">
          <div className="text-sm font-medium text-white mb-0.5">
            {months[selectedMonth]}
          </div>
          <div className="text-base font-bold text-blue-400">
            {selectedYear}
          </div>
        </div>
        <div className="h-0.5 bg-gradient-to-r from-blue-500 via-blue-400 to-blue-500"></div>
      </div>

      {isOpen && (
        <div 
          className="absolute top-full mt-2 right-0 bg-slate-900 rounded-lg shadow-2xl overflow-hidden z-50 border border-slate-700 w-48 animate-[fadeIn_0.3s_ease-out]"
          style={{ zIndex: 1002 }}
        >
          {/* Selector de año */}
          <div className="bg-slate-800 px-4 py-3 flex items-center justify-between border-b border-slate-700">
            <button 
              onClick={(e) => { e.stopPropagation(); handleYearChange(-1); }} 
              className="p-1.5 hover:bg-slate-700 rounded-lg transition-all text-white hover:scale-110"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-base font-semibold text-white">{selectedYear}</span>
            <button 
              onClick={(e) => { e.stopPropagation(); handleYearChange(1); }} 
              className="p-1.5 hover:bg-slate-700 rounded-lg transition-all text-white hover:scale-110"
            >
              <ChevronRight size={16} />
            </button>
          </div>
          {/* Grid de meses */}
          <div className="grid grid-cols-3 gap-2 p-4">
            {months.map((month, index) => (
              <button
                key={month}
                onClick={(e) => {
                  e.stopPropagation();
                  handleMonthSelect(index);
                }}
                className={`py-2 px-2 rounded-lg font-medium transition-all duration-200 text-sm ${
                  index === selectedMonth
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50 scale-105'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 hover:scale-105'
                }`}
              >
                {month.slice(0, 3)}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Componente de Ventas por Mes - Gráfico de barras
 */
const VentasPorMes = ({ selectedYear, onYearChange, facturas }) => {
  // Agrupar facturas por mes y calcular totales
  const chartData = useMemo(() => {
    const monthlyData = Array.from({ length: 12 }, (_, i) => ({
      mes: MONTH_NAMES[i],
      mesNum: i + 1,
      total: 0,
    }));

    facturas?.forEach(factura => {
      const fechaStr = factura.fecha_emision || factura.fecha;
      if (fechaStr) {
        const fecha = new Date(fechaStr);
        if (fecha.getFullYear() === selectedYear) {
          const mes = fecha.getMonth(); // 0-11
          const total = parseFloat(factura.importe_total || factura.total || 0);
          monthlyData[mes].total += total;
        }
      }
    });

    return monthlyData;
  }, [facturas, selectedYear]);

  return (
    <Box>
      {/* Gráfico de barras con efectos visuales */}
      <Box sx={{ width: '100%', height: 400 }}>
        {chartData.every(item => item.total === 0) ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
              No hay datos para el año {selectedYear}
            </Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={chartData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                {/* Gradiente para las barras */}
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#9333ea" stopOpacity={1} />
                  <stop offset="100%" stopColor="#7c3aed" stopOpacity={0.8} />
                </linearGradient>
                {/* Sombra para efecto 3D */}
                <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
                  <feOffset dx="2" dy="2" result="offsetblur" />
                  <feComponentTransfer>
                    <feFuncA type="linear" slope="0.3" />
                  </feComponentTransfer>
                  <feMerge>
                    <feMergeNode />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis 
                dataKey="mes" 
                tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500, fontFamily: "'Inter', 'Outfit', sans-serif" }}
                angle={-45}
                textAnchor="end"
                height={80}
                axisLine={{ stroke: '#e5e7eb', strokeWidth: 1 }}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500, fontFamily: "'Inter', 'Outfit', sans-serif" }}
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                axisLine={{ stroke: '#e5e7eb', strokeWidth: 1 }}
              />
              <Tooltip 
                formatter={(value) => `${parseFloat(value).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}`}
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  padding: '12px 16px',
                }}
                labelStyle={{ 
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  fontWeight: 600, 
                  color: '#1e293b',
                  marginBottom: '8px',
                }}
                cursor={{ fill: 'rgba(147, 51, 234, 0.1)' }}
              />
              <Bar 
                dataKey="total" 
                fill="url(#barGradient)"
                radius={[12, 12, 0, 0]}
                filter="url(#shadow)"
                animationDuration={800}
                animationEasing="ease-out"
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Box>
    </Box>
  );
};

/**
 * Componente de Top Proveedores - Tabla con top 10
 */
const TopProveedores = ({ selectedMonth, selectedYear, onMonthChange, onYearChange, facturas }) => {
  // Calcular top 10 proveedores del mes y año seleccionados
  const topProveedores = useMemo(() => {
    if (!facturas || facturas.length === 0) return [];

    const proveedoresMap = new Map();

    facturas.forEach(factura => {
      const fechaStr = factura.fecha_emision || factura.fecha;
      const proveedor = factura.proveedor_nombre || factura.proveedor;
      if (fechaStr && proveedor) {
        const fecha = new Date(fechaStr);
        const facturaYear = fecha.getFullYear();
        const facturaMonth = fecha.getMonth(); // 0-11
        
        // Filtrar por mes y año
        if (facturaYear === selectedYear && facturaMonth === selectedMonth) {
          const total = parseFloat(factura.importe_total || factura.total || 0);
          
          if (proveedoresMap.has(proveedor)) {
            proveedoresMap.set(proveedor, proveedoresMap.get(proveedor) + total);
          } else {
            proveedoresMap.set(proveedor, total);
          }
        }
      }
    });

    // Convertir a array, ordenar por total descendente y tomar top 10
    return Array.from(proveedoresMap.entries())
      .map(([nombre, total]) => ({ nombre, total }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10)
      .map((proveedor, index) => ({
        rank: index + 1,
        nombre: proveedor.nombre,
        total: proveedor.total,
      }));
  }, [facturas, selectedYear, selectedMonth]);

  return (
    <Box>
      {/* Tabla de proveedores */}
      {topProveedores.length === 0 ? (
        <Typography
          variant="body2"
          sx={{
            fontFamily: "'Inter', 'Outfit', sans-serif",
            color: '#64748b',
            textAlign: 'center',
            py: 4,
          }}
        >
          No hay datos para {MONTH_NAMES[selectedMonth]} {selectedYear}
        </Typography>
      ) : (
        <Box>
          {topProveedores.map((proveedor, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                mb: index < topProveedores.length - 1 ? 2 : 0,
                py: 1,
              }}
            >
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: '#3b82f6',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '0.875rem',
                  flexShrink: 0,
                }}
              >
                {proveedor.rank}
              </Box>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body1"
                  sx={{
                    fontFamily: "'Inter', 'Outfit', sans-serif",
                    fontWeight: 600,
                    color: '#1e293b',
                    fontSize: '1rem',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {proveedor.nombre}
                </Typography>
              </Box>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  fontWeight: 700,
                  color: '#1e293b',
                  fontSize: '1rem',
                  flexShrink: 0,
                }}
              >
                {proveedor.total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
};

/**
 * Componente de Tendencia Anual - Dejado en blanco por ahora
 */
const TendenciaAnual = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '200px',
      }}
    >
      <Typography
        variant="body2"
        sx={{
          fontFamily: "'Inter', 'Outfit', sans-serif",
          color: '#64748b',
          fontSize: '0.875rem',
        }}
      >
        {/* Dejado en blanco por ahora */}
      </Typography>
    </Box>
  );
};

/**
 * Página principal de Reportes
 * Envuelto en List de React-admin para que el routing funcione correctamente
 */
import { List } from 'react-admin';

export const Reportes = (props) => {
  // Inicializar con año y mes actuales
  const currentDate = new Date();
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [selectedMonthTopProveedores, setSelectedMonthTopProveedores] = useState(currentDate.getMonth()); // Mes actual (0-11)
  const [allFacturasAnio, setAllFacturasAnio] = useState([]);
  const [loading, setLoading] = useState(true);

  // Obtener facturas de todos los meses del año seleccionado
  React.useEffect(() => {
    const fetchAllMonths = async () => {
      setLoading(true);
      try {
        // Hacer llamadas paralelas para todos los meses del año
        const { fetchAllFacturas } = await import('../../../utils/api');
        const promises = Array.from({ length: 12 }, (_, i) => 
          fetchAllFacturas(i + 1, selectedYear)
        );
        
        const results = await Promise.allSettled(promises);
        const facturas = [];
        
        results.forEach((result, index) => {
          if (result.status === 'fulfilled' && result.value) {
            const facturasMes = Array.isArray(result.value) ? result.value : [];
            facturas.push(...facturasMes);
          }
        });
        
        setAllFacturasAnio(facturas);
      } catch (error) {
        console.error('Error fetching facturas:', error);
        setAllFacturasAnio([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAllMonths();
  }, [selectedYear]);

  // Filtrar facturas del año seleccionado y mapear campos de la API
  const facturasDelAnio = useMemo(() => {
    return allFacturasAnio
      .filter(factura => {
        // La API usa fecha_emision, mapear a fecha para compatibilidad
        const fechaStr = factura.fecha_emision || factura.fecha;
        if (fechaStr) {
          const fecha = new Date(fechaStr);
          return fecha.getFullYear() === selectedYear;
        }
        return false;
      })
      .map(factura => ({
        ...factura,
        // Mapear campos de la API a los nombres esperados por los componentes
        fecha: factura.fecha_emision || factura.fecha,
        proveedor: factura.proveedor_nombre || factura.proveedor,
        total: parseFloat(factura.importe_total || factura.total || 0),
      }));
  }, [allFacturasAnio, selectedYear]);

  return (
    <List {...props} title="Reportes" empty={false} actions={false}>
      <Box
        sx={{
          minHeight: '100vh',
          backgroundColor: '#f9fafb',
          padding: 0,
          margin: 0,
        }}
      >
        <div className="p-2 sm:p-4 md:p-6 lg:p-8">
          <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
            {/* Header */}
            <Box sx={{ mb: 4 }}>
              <Typography
                variant="h3"
                sx={{
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  fontWeight: 700,
                  fontSize: '2rem',
                  color: '#1e293b',
                  mb: 1,
                }}
              >
                Reportes
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  color: '#64748b',
                  fontSize: '1rem',
                }}
              >
                Panel de Reportes - Vista Modular
              </Typography>
            </Box>

            {/* Grid de tarjetas de reportes - 2 columnas en desktop, 1 en mobile */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: '1fr',
                  md: 'repeat(2, 1fr)',
                  lg: 'repeat(2, 1fr)',
                },
                gap: 3,
                mb: 3,
              }}
            >
              {/* Pago a Proveedores */}
              <ReportCard
                title="Pago a Proveedores"
                icon={BarChart3}
                color="purple"
                yearSelector={
                  <YearSelector 
                    selectedYear={selectedYear}
                    onYearChange={setSelectedYear}
                  />
                }
              >
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
                    <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                      Cargando...
                    </Typography>
                  </Box>
                ) : (
                  <VentasPorMes 
                    selectedYear={selectedYear} 
                    onYearChange={setSelectedYear}
                    facturas={facturasDelAnio} 
                  />
                )}
              </ReportCard>

              {/* Top Proveedores */}
              <ReportCard
                title="Top Proveedores"
                icon={Users}
                color="blue"
                yearSelector={
                  <MonthYearSelector 
                    selectedMonth={selectedMonthTopProveedores}
                    selectedYear={selectedYear}
                    onMonthChange={setSelectedMonthTopProveedores}
                    onYearChange={setSelectedYear}
                  />
                }
              >
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
                    <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                      Cargando...
                    </Typography>
                  </Box>
                ) : (
                  <TopProveedores 
                    selectedMonth={selectedMonthTopProveedores}
                    selectedYear={selectedYear} 
                    onMonthChange={setSelectedMonthTopProveedores}
                    onYearChange={setSelectedYear}
                    facturas={facturasDelAnio}
                  />
                )}
              </ReportCard>
            </Box>

            {/* Tendencia Anual - Abajo, ocupando ancho completo */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: '1fr',
                  md: '1fr',
                  lg: '1fr',
                },
                gap: 3,
              }}
            >
              <ReportCard
                title="Tendencia Anual"
                icon={TrendingUp}
                color="green"
              >
                <TendenciaAnual />
              </ReportCard>
            </Box>
          </div>
        </div>
      </Box>
    </List>
  );
};

