/**
 * Panel de Carga de Datos - React-admin
 * Monitoreo en tiempo real del sistema
 */
import React, { useState, useEffect } from 'react';
import { List } from 'react-admin';
import { Box, Typography, Card, CardContent, CardHeader, Button, CircularProgress } from '@mui/material';
import { 
  Cloud, 
  Database, 
  RefreshCw, 
  TrendingUp, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle,
  RefreshCcw
} from 'lucide-react';
import { Cell, PieChart, Pie, ResponsiveContainer, Legend } from 'recharts';
import { fetchDataLoadStats } from '../../../utils/api';

/**
 * Tarjeta de estadística individual
 */
const StatCard = ({ title, value, icon: Icon, color, subtitle, children }) => {
  const colorMap = {
    blue: {
      bg: '#3b82f6',
      light: '#dbeafe',
      text: '#ffffff',
    },
    green: {
      bg: '#10b981',
      light: '#d1fae5',
      text: '#ffffff',
    },
    orange: {
      bg: '#f59e0b',
      light: '#fef3c7',
      text: '#ffffff',
    },
    purple: {
      bg: '#9333ea',
      light: '#e9d5ff',
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
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 12px -2px rgba(0, 0, 0, 0.15)',
        },
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
        }}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
              }}
            >
              {title}
            </Typography>
          </Box>
        }
      />
      <CardContent
        sx={{
          padding: '24px',
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
 * Componente Gauge para estado de importación
 */
const QualityGauge = ({ percentage }) => {
  const getColor = (value) => {
    if (value >= 90) return '#10b981'; // green
    if (value >= 70) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  const getLabel = (value) => {
    if (value >= 90) return 'Excelente';
    if (value >= 70) return 'Bueno';
    return 'Requiere Atención';
  };

  const color = getColor(percentage);
  const label = getLabel(percentage);

  // Datos para el gráfico de pie (gauge)
  const data = [
    { name: 'Procesadas', value: percentage },
    { name: 'Restante', value: 100 - percentage },
  ];

  const COLORS = [color, '#e5e7eb'];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
      <Box sx={{ position: 'relative', width: '200px', height: '200px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              startAngle={90}
              endAngle={-270}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}
        >
          <Typography
            variant="h3"
            sx={{
              fontFamily: "'Inter', 'Outfit', sans-serif",
              fontWeight: 700,
              fontSize: '2.5rem',
              color: color,
              lineHeight: 1,
            }}
          >
            {percentage.toFixed(1)}%
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "'Inter', 'Outfit', sans-serif",
              color: '#64748b',
              fontSize: '0.875rem',
              mt: 0.5,
            }}
          >
            {label}
          </Typography>
        </Box>
      </Box>
      <Box sx={{ width: '100%', mt: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b', fontSize: '0.875rem' }}>
            Procesadas
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b', fontSize: '0.875rem' }}>
            Total
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

/**
 * Panel de Carga de Datos
 */
export const CargaDatosPanel = (props) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await fetchDataLoadStats();
      setStats(data);
    } catch (error) {
      console.error('Error fetching data load stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  if (loading && !stats) {
    return (
      <List {...props} title="Carga de Datos" empty={false} actions={false}>
        <Box
          sx={{
            minHeight: '100vh',
            backgroundColor: '#f9fafb',
            padding: 0,
            margin: 0,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <CircularProgress />
        </Box>
      </List>
    );
  }

  return (
    <List {...props} title="Carga de Datos" empty={false} actions={false}>
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
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
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
                  Carga de Datos
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    fontFamily: "'Inter', 'Outfit', sans-serif",
                    color: '#64748b',
                    fontSize: '1rem',
                  }}
                >
                  Monitoreo en tiempo real del sistema
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<RefreshCcw size={18} />}
                onClick={handleRefresh}
                disabled={refreshing}
                sx={{
                  backgroundColor: '#3b82f6',
                  '&:hover': {
                    backgroundColor: '#2563eb',
                  },
                }}
              >
                {refreshing ? 'Actualizando...' : 'Actualizar'}
              </Button>
            </Box>

            {/* Grid de tarjetas */}
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
              }}
            >
              {/* Tarjeta 1: Archivos en Drive */}
              <StatCard
                title="Archivos en Drive"
                icon={Cloud}
                color="blue"
              >
                <Box>
                  <Typography
                    variant="h2"
                    sx={{
                      fontFamily: "'Inter', 'Outfit', sans-serif",
                      fontWeight: 700,
                      fontSize: '3rem',
                      color: '#1e293b',
                      mb: 2,
                    }}
                  >
                    {stats?.archivos_drive?.toLocaleString() || '0'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle2 size={16} color="#10b981" />
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: "'Inter', 'Outfit', sans-serif",
                        color: '#64748b',
                        fontSize: '0.875rem',
                      }}
                    >
                      {stats?.last_sync ? `Sincronizado ${new Date(stats.last_sync).toLocaleString('es-ES')}` : 'No sincronizado'}
                    </Typography>
                  </Box>
                </Box>
              </StatCard>

              {/* Tarjeta 2: Facturas en BD */}
              <StatCard
                title="Facturas en BD"
                icon={Database}
                color="green"
              >
                <Box>
                  <Typography
                    variant="h2"
                    sx={{
                      fontFamily: "'Inter', 'Outfit', sans-serif",
                      fontWeight: 700,
                      fontSize: '3rem',
                      color: '#1e293b',
                      mb: 2,
                    }}
                  >
                    {stats?.facturas_bd?.toLocaleString() || '0'}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CheckCircle2 size={16} color="#10b981" />
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                        {stats?.facturas_procesadas?.toLocaleString() || '0'} Procesadas
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AlertTriangle size={16} color="#f59e0b" />
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                        {stats?.facturas_cuarentena?.toLocaleString() || '0'} Cuarentena
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <XCircle size={16} color="#ef4444" />
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                        {stats?.facturas_error?.toLocaleString() || '0'} Error
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </StatCard>

              {/* Tarjeta 3: Sincronización */}
              <StatCard
                title="Sincronización"
                icon={RefreshCw}
                color="orange"
              >
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                        Archivos Drive
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", fontWeight: 600, color: '#1e293b' }}>
                        {stats?.archivos_drive?.toLocaleString() || '0'}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b' }}>
                        Facturas BD
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", fontWeight: 600, color: '#1e293b' }}>
                        {stats?.facturas_bd?.toLocaleString() || '0'}
                      </Typography>
                    </Box>
                  </Box>
                  <Box
                    sx={{
                      padding: '16px',
                      borderRadius: '12px',
                      backgroundColor: stats?.diferencia === 0 ? '#d1fae5' : '#fef3c7',
                      border: `1px solid ${stats?.diferencia === 0 ? '#10b981' : '#f59e0b'}`,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="body1" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", fontWeight: 600, color: '#1e293b' }}>
                        Diferencia
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {stats?.diferencia === 0 ? (
                          <CheckCircle2 size={20} color="#10b981" />
                        ) : (
                          <TrendingUp size={20} color="#f59e0b" />
                        )}
                        <Typography
                          variant="h6"
                          sx={{
                            fontFamily: "'Inter', 'Outfit', sans-serif",
                            fontWeight: 700,
                            color: stats?.diferencia === 0 ? '#10b981' : '#f59e0b',
                          }}
                        >
                          {stats?.diferencia && stats.diferencia > 0 ? '+' : ''}
                          {stats?.diferencia?.toLocaleString() || '0'}
                        </Typography>
                      </Box>
                    </Box>
                    {stats?.diferencia !== 0 && (
                      <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b', mt: 1, fontSize: '0.75rem' }}>
                        {stats.diferencia > 0 ? 'Más archivos en Drive' : 'Más facturas en BD'}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </StatCard>

              {/* Tarjeta 4: Estado de Importación de Facturas */}
              <StatCard
                title="Estado de Importación"
                icon={TrendingUp}
                color="purple"
              >
                <QualityGauge percentage={stats?.nivel_calidad || 0} />
                <Box sx={{ mt: 3, textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ fontFamily: "'Inter', 'Outfit', sans-serif", color: '#64748b', fontSize: '0.875rem' }}>
                    {stats?.facturas_procesadas?.toLocaleString() || '0'} procesadas de {stats?.archivos_drive?.toLocaleString() || '0'} archivos en Drive
                  </Typography>
                </Box>
              </StatCard>
            </Box>
          </div>
        </div>
      </Box>
    </List>
  );
};
