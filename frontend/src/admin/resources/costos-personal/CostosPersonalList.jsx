/**
 * Costos de Personal - Vista principal
 * Gestión de costos mensuales de nómina y seguridad social
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import { Edit, Trash2, Plus } from 'lucide-react';
import { useGetList, useCreate, useUpdate, useDelete } from 'react-admin';
import { SPACING, PAGE_LAYOUT, COLORS, BORDER_RADIUS } from '../../styles/designTokens';
import { BaseCard } from '../../../components/ui';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';

// Nombres de meses en español
const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const MESES_ABREV = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
];

/**
 * Formato de moneda en euros
 */
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Componente de formulario modal para crear/editar costos
 */
const CostoFormModal = ({ open, onClose, onSave, initialData, year }) => {
  const [formData, setFormData] = useState({
    mes: initialData?.mes || new Date().getMonth() + 1,
    año: initialData?.año || year,
    sueldos_netos: initialData?.sueldos_netos || 0,
    coste_empresa: initialData?.coste_empresa || 0,
    notas: initialData?.notas || '',
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  React.useEffect(() => {
    if (initialData) {
      // Si tiene sueldos_netos o coste_empresa, es un costo existente
      if (initialData.sueldos_netos !== undefined || initialData.coste_empresa !== undefined) {
        setFormData({
          mes: initialData.mes,
          año: initialData.año,
          sueldos_netos: initialData.sueldos_netos || 0,
          coste_empresa: initialData.coste_empresa || 0,
          notas: initialData.notas || '',
        });
      } else {
        // Es solo mes/año para crear nuevo
        setFormData({
          mes: initialData.mes,
          año: initialData.año,
          sueldos_netos: 0,
          coste_empresa: 0,
          notas: '',
        });
      }
    } else {
      setFormData({
        mes: new Date().getMonth() + 1,
        año: year,
        sueldos_netos: 0,
        coste_empresa: 0,
        notas: '',
      });
    }
  }, [initialData, year]);

  const totalPersonal = formData.sueldos_netos + formData.coste_empresa;

  const validate = () => {
    const newErrors = {};
    if (formData.mes < 1 || formData.mes > 12) {
      newErrors.mes = 'El mes debe estar entre 1 y 12';
    }
    if (formData.año < 2000 || formData.año > 2100) {
      newErrors.año = 'El año debe estar entre 2000 y 2100';
    }
    if (formData.sueldos_netos < 0) {
      newErrors.sueldos_netos = 'Los sueldos netos no pueden ser negativos';
    }
    if (formData.coste_empresa < 0) {
      newErrors.coste_empresa = 'El coste de empresa no puede ser negativo';
    }
    if (formData.notas && formData.notas.length > 500) {
      newErrors.notas = 'Las notas no pueden exceder 500 caracteres';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error al guardar:', error);
      setErrors({ submit: error.message || 'Error al guardar el costo' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {initialData ? 'Editar Costo de Personal' : 'Cargar Costos de Personal'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
          {errors.submit && (
            <Alert severity="error">{errors.submit}</Alert>
          )}

          <FormControl fullWidth error={!!errors.mes}>
            <InputLabel>Mes</InputLabel>
            <Select
              value={formData.mes}
              label="Mes"
              onChange={(e) => setFormData({ ...formData, mes: e.target.value })}
            >
              {MESES.map((mes, index) => (
                <MenuItem key={index + 1} value={index + 1}>
                  {mes}
                </MenuItem>
              ))}
            </Select>
            {errors.mes && <Typography variant="caption" color="error">{errors.mes}</Typography>}
          </FormControl>

          <TextField
            label="Año"
            type="number"
            value={formData.año}
            onChange={(e) => setFormData({ ...formData, año: parseInt(e.target.value) || 0 })}
            error={!!errors.año}
            helperText={errors.año}
            fullWidth
            inputProps={{ min: 2000, max: 2100 }}
          />

          <TextField
            label="Sueldos Netos (€)"
            type="number"
            value={formData.sueldos_netos}
            onChange={(e) => setFormData({ ...formData, sueldos_netos: parseFloat(e.target.value) || 0 })}
            error={!!errors.sueldos_netos}
            helperText={errors.sueldos_netos}
            fullWidth
            inputProps={{ min: 0, step: 0.01 }}
          />

          <TextField
            label="Coste Empresa - Seguros Sociales (€)"
            type="number"
            value={formData.coste_empresa}
            onChange={(e) => setFormData({ ...formData, coste_empresa: parseFloat(e.target.value) || 0 })}
            error={!!errors.coste_empresa}
            helperText={errors.coste_empresa}
            fullWidth
            inputProps={{ min: 0, step: 0.01 }}
          />

          <Box
            sx={{
              p: 2,
              backgroundColor: COLORS.success.light,
              borderRadius: BORDER_RADIUS.md,
              border: `1px solid ${COLORS.success.main}`,
            }}
          >
            <Typography variant="body2" color={COLORS.success.dark} fontWeight={600}>
              Total Personal: {formatCurrency(totalPersonal)}
            </Typography>
          </Box>

          <TextField
            label="Notas (opcional)"
            multiline
            rows={3}
            value={formData.notas}
            onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
            error={!!errors.notas}
            helperText={errors.notas || 'Máximo 500 caracteres'}
            fullWidth
            inputProps={{ maxLength: 500 }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saving}
          sx={{ backgroundColor: COLORS.primary.main }}
        >
          {saving ? <CircularProgress size={20} /> : 'Guardar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Componente principal de Costos de Personal
 */
export const CostosPersonalList = () => {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCosto, setEditingCosto] = useState(null);
  const [totales, setTotales] = useState(null);
  const [loadingTotales, setLoadingTotales] = useState(false);
  const [savingForm, setSavingForm] = useState(false);
  const [formData, setFormData] = useState({
    mes: new Date().getMonth() + 1,
    año: new Date().getFullYear(),
    sueldos_netos: 0,
    coste_empresa: 0,
    notas: '',
  });

  // Obtener costos del año seleccionado
  const { data: costos, isLoading, refetch } = useGetList('costos-personal', {
    pagination: { page: 1, perPage: 12 },
    sort: { field: 'mes', order: 'ASC' },
    filter: { year: selectedYear },
  });

  // Actualizar año del formulario cuando cambia el año seleccionado
  React.useEffect(() => {
    setFormData((prev) => ({ ...prev, año: selectedYear }));
  }, [selectedYear]);

  const [create] = useCreate();
  const [update] = useUpdate();
  const [deleteOne] = useDelete();

  // Cargar totales del año
  React.useEffect(() => {
    const loadTotales = async () => {
      setLoadingTotales(true);
      try {
        const response = await fetch(
          `${API_BASE_URL}/costos-personal/${selectedYear}/totales`,
          {
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
          }
        );
        if (response.ok) {
          const data = await response.json();
          setTotales(data);
        }
      } catch (error) {
        console.error('Error al cargar totales:', error);
      } finally {
        setLoadingTotales(false);
      }
    };

    loadTotales();
  }, [selectedYear, costos]);

  // Crear mapa de costos por mes para acceso rápido
  const costosPorMes = useMemo(() => {
    const mapa = {};
    (costos || []).forEach((costo) => {
      mapa[costo.mes] = costo;
    });
    return mapa;
  }, [costos]);

  // Calcular estadísticas
  const estadisticas = useMemo(() => {
    if (!costos || costos.length === 0) {
      return {
        total: 0,
        promedio: 0,
        maximo: 0,
        minimo: 0,
      };
    }

    const totales = costos.map((c) => c.total_personal || 0);
    const total = totales.reduce((sum, val) => sum + val, 0);
    const promedio = total / totales.length;
    const maximo = Math.max(...totales);
    const minimo = Math.min(...totales);

    return { total, promedio, maximo, minimo };
  }, [costos]);

  const handleOpenModal = (mes = null) => {
    if (mes && costosPorMes[mes]) {
      // Editar costo existente
      setEditingCosto(costosPorMes[mes]);
    } else if (mes) {
      // Crear nuevo costo para un mes específico
      setEditingCosto({ mes, año: selectedYear });
    } else {
      // Crear nuevo costo sin mes específico
      setEditingCosto(null);
    }
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingCosto(null);
  };

  const handleSave = async (formData) => {
    if (editingCosto) {
      await update('costos-personal', {
        id: editingCosto.id,
        data: formData,
      });
    } else {
      await create('costos-personal', {
        data: formData,
      });
    }
    refetch();
  };

  const handleSaveForm = async () => {
    if (formData.sueldos_netos < 0 || formData.coste_empresa < 0) {
      alert('Los valores no pueden ser negativos');
      return;
    }
    if (formData.mes < 1 || formData.mes > 12) {
      alert('El mes debe estar entre 1 y 12');
      return;
    }

    setSavingForm(true);
    try {
      const dataToSave = {
        mes: formData.mes,
        año: formData.año,
        sueldos_netos: formData.sueldos_netos,
        coste_empresa: formData.coste_empresa,
        notas: formData.notas || '',
      };

      // Verificar si ya existe un costo para este mes/año
      const existingCosto = costosPorMes[formData.mes];
      if (existingCosto && existingCosto.año === formData.año) {
        await update('costos-personal', {
          id: existingCosto.id,
          data: dataToSave,
        });
      } else {
        await create('costos-personal', {
          data: dataToSave,
        });
      }

      // Limpiar formulario después de guardar
      setFormData({
        mes: new Date().getMonth() + 1,
        año: selectedYear,
        sueldos_netos: 0,
        coste_empresa: 0,
        notas: '',
      });

      refetch();
    } catch (error) {
      console.error('Error al guardar:', error);
      alert('Error al guardar los costos. Por favor, intente nuevamente.');
    } finally {
      setSavingForm(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este costo?')) {
      try {
        await deleteOne('costos-personal', { id });
        refetch();
      } catch (error) {
        console.error('Error al eliminar:', error);
        alert('Error al eliminar el costo');
      }
    }
  };

  // Obtener color según el valor del mes
  const getMonthColor = (total) => {
    if (!total || total === 0) return COLORS.background.paper;
    const { promedio, maximo } = estadisticas;
    if (total === maximo) return '#fef3c7'; // Amarillo claro para máximo
    if (total > promedio * 1.1) return '#fde68a'; // Amarillo más intenso
    return '#d1fae5'; // Verde claro para valores normales
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: COLORS.background.default,
        padding: 0,
        margin: 0,
      }}
    >
      <Box sx={{ p: { xs: 1, sm: 2, md: 3, lg: 4 } }}>
        <Box sx={{ mx: 'auto', px: { xs: 1.5, sm: 2, md: 2.5, lg: 3 } }}>
          {/* Título y selector de año */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: PAGE_LAYOUT.sectionSpacing,
              mt: PAGE_LAYOUT.titleMarginTop,
            }}
          >
            <Box>
              <Typography
                variant="h3"
                sx={{
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  fontWeight: 700,
                  fontSize: '2rem',
                  color: COLORS.text.primary,
                  mb: 1,
                }}
              >
                Costos de Personal
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  fontFamily: "'Inter', 'Outfit', sans-serif",
                  color: COLORS.text.secondary,
                  fontSize: '1rem',
                }}
              >
                Gestión de costos mensuales de nómina y seguridad social
              </Typography>
            </Box>
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Año</InputLabel>
              <Select
                value={selectedYear}
                label="Año"
                onChange={(e) => setSelectedYear(e.target.value)}
              >
                {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 5 + i).map((year) => (
                  <MenuItem key={year} value={year}>
                    {year}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Tarjeta de totales */}
          <BaseCard
            sx={{
              mb: PAGE_LAYOUT.sectionSpacing,
              backgroundColor: '#1e3a8a',
              color: '#ffffff',
            }}
            contentSx={{ p: 4 }}
          >
            <Typography
              variant="h4"
              sx={{
                color: '#ffffff',
                fontWeight: 700,
                mb: 3,
                fontSize: '1.5rem',
              }}
            >
              Resumen Anual {selectedYear}
            </Typography>
            {loadingTotales ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress sx={{ color: '#ffffff' }} />
              </Box>
            ) : (
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" sx={{ color: '#93c5fd', mb: 1 }}>
                      Total Anual
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 700 }}>
                      {formatCurrency(totales?.total_personal || estadisticas.total)}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" sx={{ color: '#93c5fd', mb: 1 }}>
                      Promedio
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 700 }}>
                      {formatCurrency(estadisticas.promedio)}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" sx={{ color: '#fbbf24', mb: 1 }}>
                      Máximo
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#fbbf24', fontWeight: 700 }}>
                      {formatCurrency(estadisticas.maximo)}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box>
                    <Typography variant="body2" sx={{ color: '#34d399', mb: 1 }}>
                      Mínimo
                    </Typography>
                    <Typography variant="h5" sx={{ color: '#34d399', fontWeight: 700 }}>
                      {formatCurrency(estadisticas.minimo)}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            )}
          </BaseCard>

          {/* Tarjeta de meses */}
          <BaseCard
            title="Visualización Anual"
            sx={{ mb: PAGE_LAYOUT.sectionSpacing }}
          >
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Grid container spacing={2}>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((mes) => {
                  const costo = costosPorMes[mes];
                  const total = costo?.total_personal || 0;
                  const hasData = !!costo;

                  return (
                    <Grid item xs={6} sm={4} md={3} key={mes}>
                      <Card
                        sx={{
                          backgroundColor: getMonthColor(total),
                          border: hasData
                            ? `2px solid ${COLORS.primary.main}`
                            : `1px solid ${COLORS.border.default}`,
                          borderRadius: BORDER_RADIUS.lg,
                          p: 2,
                          position: 'relative',
                          transition: 'transform 0.2s, box-shadow 0.2s',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                          },
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.875rem',
                              color: COLORS.text.primary,
                            }}
                          >
                            {MESES_ABREV[mes - 1]}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            {hasData && (
                              <>
                                <IconButton
                                  size="small"
                                  onClick={() => handleOpenModal(mes)}
                                  sx={{ p: 0.5 }}
                                >
                                  <Edit size={14} color={COLORS.primary.main} />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  onClick={() => handleDelete(costo.id)}
                                  sx={{ p: 0.5 }}
                                >
                                  <Trash2 size={14} color={COLORS.error.main} />
                                </IconButton>
                              </>
                            )}
                            {!hasData && (
                              <IconButton
                                size="small"
                                onClick={() => handleOpenModal(mes)}
                                sx={{ p: 0.5 }}
                              >
                                <Plus size={14} color={COLORS.primary.main} />
                              </IconButton>
                            )}
                          </Box>
                        </Box>
                        <Typography
                          variant="body1"
                          sx={{
                            fontWeight: 600,
                            fontSize: '1rem',
                            color: hasData ? COLORS.text.primary : COLORS.text.secondary,
                          }}
                        >
                          {hasData ? formatCurrency(total) : 'Sin datos'}
                        </Typography>
                        {hasData && (
                          <Typography
                            variant="caption"
                            sx={{
                              color: COLORS.text.secondary,
                              fontSize: '0.75rem',
                              display: 'block',
                              mt: 0.5,
                            }}
                          >
                            Netos: {formatCurrency(costo.sueldos_netos)}
                            <br />
                            Empresa: {formatCurrency(costo.coste_empresa)}
                          </Typography>
                        )}
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </BaseCard>

          {/* Formulario para ingresar costos */}
          <BaseCard
            title="Cargar Costos de Personal"
            sx={{ mb: PAGE_LAYOUT.sectionSpacing }}
          >
            <Box
              component="form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSaveForm();
              }}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 3,
              }}
            >
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Mes</InputLabel>
                    <Select
                      value={formData.mes}
                      label="Mes"
                      onChange={(e) => setFormData({ ...formData, mes: e.target.value })}
                    >
                      {MESES.map((mes, index) => (
                        <MenuItem key={index + 1} value={index + 1}>
                          {mes}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    label="Sueldos Netos (€)"
                    type="number"
                    value={formData.sueldos_netos}
                    onChange={(e) => setFormData({ ...formData, sueldos_netos: parseFloat(e.target.value) || 0 })}
                    fullWidth
                    inputProps={{ min: 0, step: 0.01 }}
                    helperText="Total de sueldos netos pagados al personal"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    label="Coste Empresa - Seguridad Social (€)"
                    type="number"
                    value={formData.coste_empresa}
                    onChange={(e) => setFormData({ ...formData, coste_empresa: parseFloat(e.target.value) || 0 })}
                    fullWidth
                    inputProps={{ min: 0, step: 0.01 }}
                    helperText="Total de seguros sociales y cotizaciones"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box
                    sx={{
                      p: 2,
                      backgroundColor: COLORS.success.light,
                      borderRadius: BORDER_RADIUS.md,
                      border: `1px solid ${COLORS.success.main}`,
                      mb: 2,
                    }}
                  >
                    <Typography variant="body2" color={COLORS.success.dark} fontWeight={600}>
                      Total Personal: {formatCurrency(formData.sueldos_netos + formData.coste_empresa)}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      type="button"
                      variant="outlined"
                      onClick={() => {
                        setFormData({
                          mes: new Date().getMonth() + 1,
                          año: selectedYear,
                          sueldos_netos: 0,
                          coste_empresa: 0,
                          notas: '',
                        });
                      }}
                    >
                      Limpiar
                    </Button>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={savingForm}
                      sx={{
                        backgroundColor: COLORS.primary.main,
                        '&:hover': {
                          backgroundColor: COLORS.primary.dark,
                        },
                      }}
                    >
                      {savingForm ? <CircularProgress size={20} /> : 'Guardar Costos'}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </BaseCard>

          {/* Formulario modal */}
          <CostoFormModal
            open={modalOpen}
            onClose={handleCloseModal}
            onSave={handleSave}
            initialData={editingCosto}
            year={selectedYear}
          />
        </Box>
      </Box>
    </Box>
  );
};

