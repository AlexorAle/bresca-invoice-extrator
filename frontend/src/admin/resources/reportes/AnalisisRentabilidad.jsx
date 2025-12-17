/**
 * Componente de Análisis de Rentabilidad
 * Muestra KPIs, gráfico y tabla con edición inline de ingresos
 */
import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  TextField, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { TrendingUp, DollarSign, TrendingDown, Percent, Save, XCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { MONTH_NAMES } from '../../../utils/constants';
import { COLORS, BORDER_RADIUS, SPACING } from '../../../admin/styles/designTokens';
import { BaseButton } from '../../../components/ui';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';

/**
 * Formatea un número en formato €Xk
 */
const formatEuros = (value) => {
  if (value === 0) return '€0';
  const k = value / 1000;
  if (k >= 1) {
    return `€${k.toFixed(1)}k`;
  }
  return `€${value.toFixed(0)}`;
};

/**
 * Componente de KPI individual
 */
const KPICard = ({ icon: Icon, label, value, color, formatValue = (v) => v }) => {
  const colorMap = {
    green: { bg: COLORS.success.light, icon: COLORS.success.main, text: COLORS.success.dark },
    red: { bg: COLORS.error.light, icon: COLORS.error.main, text: COLORS.error.dark },
    blue: { bg: COLORS.info.light, icon: COLORS.info.main, text: COLORS.info.dark },
    purple: { bg: COLORS.warning.light, icon: COLORS.warning.main, text: COLORS.warning.dark },
  };
  
  const colors = colorMap[color] || colorMap.blue;
  
  return (
    <Box
      sx={{
        backgroundColor: colors.bg,
        borderRadius: BORDER_RADIUS.lg,
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        minHeight: '80px',
        justifyContent: 'center',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
        <Icon size={16} color={colors.icon} />
        <Typography
          variant="body2"
          sx={{
            fontFamily: "'Inter', 'Outfit', sans-serif",
            fontWeight: 600,
            color: colors.text,
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {label}
        </Typography>
      </Box>
      <Typography
        variant="h6"
        sx={{
          fontFamily: "'Inter', 'Outfit', sans-serif",
          fontWeight: 700,
          color: colors.text,
          fontSize: '1.25rem',
          lineHeight: 1.2,
          mt: 0.5,
        }}
      >
        {formatValue(value)}
      </Typography>
    </Box>
  );
};

export const AnalisisRentabilidad = ({ selectedYear }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [confirmDialog, setConfirmDialog] = useState(null);
  const [saving, setSaving] = useState(false);

  // Cargar datos de rentabilidad
  useEffect(() => {
    const fetchRentabilidad = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/ingresos/rentabilidad/${selectedYear}`, {
          credentials: 'include', // Importante: incluir cookies de sesión
        });
        if (!response.ok) throw new Error('Error al cargar datos');
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Error fetching rentabilidad:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRentabilidad();
  }, [selectedYear]);

  // Datos para el gráfico
  const chartData = useMemo(() => {
    if (!data) return [];
    return data.meses.map(mes => ({
      mes: MONTH_NAMES[mes.mes - 1],
      Ingresos: mes.ingresos,
      Gastos: mes.gastos,
      Rentabilidad: mes.rentabilidad,
    }));
  }, [data]);

  // Manejar inicio de edición
  const handleEditStart = (mesIndex) => {
    const mes = data.meses[mesIndex];
    setEditingCell(mesIndex);
    setEditValue(mes.ingresos.toString());
  };

  // Manejar cancelar edición
  const handleEditCancel = () => {
    setEditingCell(null);
    setEditValue('');
  };

  // Manejar guardar
  const handleSave = async (mesIndex) => {
    const mes = data.meses[mesIndex];
    const newValue = parseFloat(editValue);
    
    if (isNaN(newValue) || newValue < 0) {
      alert('Por favor ingresa un valor numérico válido mayor o igual a 0');
      return;
    }

    // Mostrar modal de confirmación
    setConfirmDialog({
      mes: MONTH_NAMES[mes.mes - 1],
      año: mes.año,
      nuevoMonto: newValue,
      mesIndex: mesIndex,
    });
  };

  // Confirmar y guardar
  const handleConfirmSave = async () => {
    if (!confirmDialog) return;
    
    const { mesIndex, nuevoMonto } = confirmDialog;
    const mes = data.meses[mesIndex];
    
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/ingresos/upsert`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Importante: incluir cookies de sesión
        body: JSON.stringify({
          mes: mes.mes,
          año: mes.año,
          monto_ingresos: nuevoMonto,
        }),
      });

      if (!response.ok) throw new Error('Error al guardar');

      // Recargar datos
      const rentResponse = await fetch(`${API_BASE_URL}/ingresos/rentabilidad/${selectedYear}`, {
        credentials: 'include', // Importante: incluir cookies de sesión
      });
      const rentData = await rentResponse.json();
      setData(rentData);

      // Limpiar estado
      setEditingCell(null);
      setEditValue('');
      setConfirmDialog(null);
    } catch (error) {
      console.error('Error saving:', error);
      alert('Error al guardar el ingreso');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return (
      <Box sx={{ p: 2, textAlign: 'center', color: '#64748b' }}>
        No se pudieron cargar los datos de rentabilidad
      </Box>
    );
  }

  return (
    <Box>
      {/* KPIs */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 1.5,
          mb: 2.5,
        }}
      >
        <KPICard
          icon={DollarSign}
          label="Ingresos Totales"
          value={data.totales.ingresos}
          color="green"
          formatValue={formatEuros}
        />
        <KPICard
          icon={TrendingDown}
          label="Gastos Totales"
          value={data.totales.gastos}
          color="red"
          formatValue={formatEuros}
        />
        <KPICard
          icon={TrendingUp}
          label="Rentabilidad Neta"
          value={data.totales.rentabilidad}
          color="blue"
          formatValue={formatEuros}
        />
        <KPICard
          icon={Percent}
          label="Margen Promedio"
          value={data.totales.margen}
          color="purple"
          formatValue={(v) => `${v.toFixed(1)}%`}
        />
      </Box>

      {/* Gráfico de barras agrupadas */}
      <Box sx={{ mb: 2.5 }}>
        <Typography
          variant="subtitle1"
          sx={{
            fontFamily: "'Inter', 'Outfit', sans-serif",
            fontWeight: 600,
            fontSize: '0.9375rem',
            color: '#1e293b',
            mb: 1.5,
          }}
        >
          Comparativa Mensual
        </Typography>
        <Box sx={{ width: '100%', height: '240px' }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="mes" 
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickMargin={8}
              />
              <YAxis 
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickMargin={8}
              />
              <Tooltip 
                formatter={(value) => `€${value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                contentStyle={{ 
                  backgroundColor: '#ffffff', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '6px',
                  fontSize: '12px',
                  padding: '8px 12px'
                }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '12px' }}
                iconSize={12}
                style={{ fontSize: '12px' }}
              />
              <Bar dataKey="Ingresos" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Gastos" fill="#f87171" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Rentabilidad" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Box>

      {/* Tabla de detalle mensual */}
      <Box>
        <Typography
          variant="subtitle1"
          sx={{
            fontFamily: "'Inter', 'Outfit', sans-serif",
            fontWeight: 600,
            fontSize: '0.9375rem',
            color: '#1e293b',
            mb: 1.5,
          }}
        >
          Detalle Mensual
        </Typography>
        <Box
          sx={{
            backgroundColor: COLORS.background.paper,
            borderRadius: BORDER_RADIUS.lg,
            border: `1px solid ${COLORS.border.default}`,
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <TableRow sx={{ backgroundColor: COLORS.background.subtle }}>
                <TableCell sx={{ 
                  padding: '10px 12px', 
                  textAlign: 'left', 
                  fontWeight: 600, 
                  fontSize: '0.75rem', 
                  color: COLORS.text.secondary, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}>
                  Mes
                </TableCell>
                <TableCell sx={{ 
                  padding: '10px 12px', 
                  textAlign: 'right', 
                  fontWeight: 600, 
                  fontSize: '0.75rem', 
                  color: COLORS.text.secondary, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}>
                  Ingresos
                </TableCell>
                <TableCell sx={{ 
                  padding: '10px 12px', 
                  textAlign: 'right', 
                  fontWeight: 600, 
                  fontSize: '0.75rem', 
                  color: COLORS.text.secondary, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}>
                  Gastos
                </TableCell>
                <TableCell sx={{ 
                  padding: '10px 12px', 
                  textAlign: 'right', 
                  fontWeight: 600, 
                  fontSize: '0.75rem', 
                  color: COLORS.text.secondary, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}>
                  Rentabilidad
                </TableCell>
                <TableCell sx={{ 
                  padding: '10px 12px', 
                  textAlign: 'right', 
                  fontWeight: 600, 
                  fontSize: '0.75rem', 
                  color: COLORS.text.secondary, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px' 
                }}>
                  Margen
                </TableCell>
              </TableRow>
            </thead>
            <tbody>
              {data.meses.map((mes, index) => {
                const isEditing = editingCell === index;
                const isDefault = !mes.ingreso_cargado;
                
                return (
                  <tr
                    key={index}
                    style={{
                      borderBottom: '1px solid #e5e7eb',
                      backgroundColor: isDefault ? '#f9fafb' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontSize: '0.8125rem', fontWeight: 500, color: '#1e293b' }}>
                      {MONTH_NAMES[mes.mes - 1]}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      {isEditing ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, justifyContent: 'flex-end' }}>
                          <TextField
                            type="number"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            size="small"
                            sx={{ width: '100px', '& .MuiInputBase-input': { fontSize: '0.8125rem', padding: '6px 8px' } }}
                            inputProps={{ min: 0, step: 0.01 }}
                            autoFocus
                          />
                          <BaseButton
                            size="icon"
                            variant="contained"
                            startIcon={<Save size={12} />}
                            onClick={() => handleSave(index)}
                            sx={{
                              backgroundColor: COLORS.success.main,
                              fontSize: '0.75rem',
                              padding: '4px 12px',
                              minWidth: 'auto',
                              height: 'auto',
                              '&:hover': { backgroundColor: COLORS.success.dark },
                            }}
                          >
                            Guardar
                          </BaseButton>
                          <BaseButton
                            size="icon"
                            variant="outlined"
                            startIcon={<XCircle size={12} />}
                            onClick={handleEditCancel}
                            sx={{
                              borderColor: COLORS.error.main,
                              color: COLORS.error.main,
                              fontSize: '0.75rem',
                              padding: '4px 12px',
                              minWidth: 'auto',
                              height: 'auto',
                              '&:hover': { 
                                borderColor: COLORS.error.dark, 
                                backgroundColor: COLORS.error.light 
                              },
                            }}
                          >
                            Cancelar
                          </BaseButton>
                        </Box>
                      ) : (
                        <Typography
                          onClick={() => handleEditStart(index)}
                          sx={{
                            fontFamily: "'Inter', 'Outfit', sans-serif",
                            fontSize: '0.8125rem',
                            fontWeight: 600,
                            color: isDefault ? '#64748b' : '#10b981',
                            cursor: 'pointer',
                            '&:hover': { textDecoration: 'underline' },
                          }}
                        >
                          €{mes.ingresos.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </Typography>
                      )}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', fontSize: '0.8125rem', color: '#64748b', fontWeight: 500 }}>
                      €{mes.gastos.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      <Typography
                        sx={{
                          fontFamily: "'Inter', 'Outfit', sans-serif",
                          fontSize: '0.8125rem',
                          fontWeight: 600,
                          color: mes.rentabilidad >= 0 ? '#3b82f6' : '#ef4444',
                        }}
                      >
                        €{mes.rentabilidad.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Typography>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right', fontSize: '0.8125rem', color: '#64748b', fontWeight: 500 }}>
                      {mes.margen.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Box>
      </Box>

      {/* Modal de confirmación */}
      <Dialog
        open={!!confirmDialog}
        onClose={() => setConfirmDialog(null)}
        PaperProps={{
          sx: {
            borderRadius: '12px',
            padding: '8px',
          },
        }}
      >
        <DialogTitle
          sx={{
            fontFamily: "'Inter', 'Outfit', sans-serif",
            fontWeight: 600,
            fontSize: '1.25rem',
          }}
        >
          Confirmar Cambio
        </DialogTitle>
        <DialogContent>
          <Typography
            sx={{
              fontFamily: "'Inter', 'Outfit', sans-serif",
              fontSize: '1rem',
              color: '#374151',
            }}
          >
            ¿Confirmas el ingreso de <strong>€{confirmDialog?.nuevoMonto.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong> para{' '}
            <strong>{confirmDialog?.mes} {confirmDialog?.año}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ padding: '16px 24px', gap: 1 }}>
          <Button
            onClick={() => setConfirmDialog(null)}
            variant="outlined"
            sx={{
              borderColor: '#64748b',
              color: '#64748b',
            }}
          >
            Cancelar
          </Button>
          <BaseButton
            onClick={handleConfirmSave}
            variant="contained"
            disabled={saving}
            sx={{
              backgroundColor: COLORS.success.main,
              '&:hover': { backgroundColor: COLORS.success.dark },
            }}
          >
            {saving ? 'Guardando...' : 'Confirmar'}
          </BaseButton>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
