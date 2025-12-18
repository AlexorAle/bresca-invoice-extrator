/**
 * Componente Modal para edición manual de facturas pendientes
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Autocomplete,
  ListItemText,
} from '@mui/material';
import { X, Save, FileText } from 'lucide-react';
import { createManualInvoice } from '../utils/api';

// API Base URL (mismo que en otros componentes)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';

export const ManualInvoiceForm = ({ open, onClose, invoice, onSuccess }) => {
  const [formData, setFormData] = useState({
    proveedor_text: '',
    fecha_emision: '',
    importe_total: '',
    impuestos_total: '',
    numero_factura: '',
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [proveedoresOptions, setProveedoresOptions] = useState([]);
  const [proveedorLoading, setProveedorLoading] = useState(false);

  // Cargar datos de la factura cuando se abre el modal
  useEffect(() => {
    if (open && invoice) {
      // Formatear fecha si existe
      let fechaFormateada = '';
      if (invoice.fecha_emision) {
        const fecha = new Date(invoice.fecha_emision);
        fechaFormateada = fecha.toISOString().split('T')[0];
      }

      setFormData({
        proveedor_text: invoice.proveedor_text || '',
        fecha_emision: fechaFormateada,
        importe_total: invoice.importe_total || '',
        impuestos_total: invoice.impuestos_total || '',
        numero_factura: invoice.numero_factura || '',
      });

      setErrors({});
      setSubmitError(null);

      // Intentar obtener URL del PDF si existe
      if (invoice.drive_file_name) {
        // Construir URL del PDF (ajustar según tu configuración)
        // Por ahora, dejamos null ya que necesitaríamos el endpoint correcto
        setPdfUrl(null);
      }
    }
  }, [open, invoice]);

  // Autocompletado de proveedores
  const searchProveedores = useCallback(async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      setProveedoresOptions([]);
      return;
    }

    try {
      setProveedorLoading(true);
      // URL correcta: /invoice-api/api/proveedores/autocomplete
      const url = `${API_BASE_URL}/proveedores/autocomplete?q=${encodeURIComponent(searchTerm)}&limit=10`;
      console.log('🔍 Buscando proveedores:', url);
      
      const response = await fetch(url, { 
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('📡 Respuesta del servidor:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Proveedores encontrados:', data.length, data);
        setProveedoresOptions(data);
      } else {
        console.error('❌ Error en respuesta:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('❌ Error detalle:', errorText);
        setProveedoresOptions([]);
      }
    } catch (error) {
      console.error('❌ Error buscando proveedores:', error);
      setProveedoresOptions([]);
    } finally {
      setProveedorLoading(false);
    }
  }, []);

  // Debounce para búsqueda de proveedores
  useEffect(() => {
    const searchTerm = formData.proveedor_text?.trim() || '';
    console.log('⏱️ Debounce effect:', { searchTerm, length: searchTerm.length });
    
    const timeoutId = setTimeout(() => {
      if (searchTerm.length >= 2) {
        console.log('🚀 Ejecutando búsqueda después de debounce:', searchTerm);
        searchProveedores(searchTerm);
      } else {
        console.log('🧹 Limpiando opciones (menos de 2 caracteres)');
        setProveedoresOptions([]);
      }
    }, 300);

    return () => {
      console.log('🧹 Limpiando timeout');
      clearTimeout(timeoutId);
    };
  }, [formData.proveedor_text, searchProveedores]);

  // Validar que impuestos no sea mayor que el total
  useEffect(() => {
    if (formData.impuestos_total && formData.importe_total) {
      const impuestos = parseFloat(formData.impuestos_total) || 0;
      const total = parseFloat(formData.importe_total) || 0;
      
      if (impuestos > total) {
        setErrors(prev => ({
          ...prev,
          impuestos_total: `Los impuestos no pueden ser mayores que el total (${total.toFixed(2)})`,
        }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.impuestos_total;
          return newErrors;
        });
      }
    }
  }, [formData.impuestos_total, formData.importe_total]);

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Limpiar error del campo al cambiar
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validar campos obligatorios
    if (!formData.proveedor_text || !formData.proveedor_text.trim()) {
      newErrors.proveedor_text = 'El proveedor es obligatorio';
    }

    if (!formData.fecha_emision) {
      newErrors.fecha_emision = 'La fecha de emisión es obligatoria';
    }

    if (!formData.importe_total || parseFloat(formData.importe_total) <= 0) {
      newErrors.importe_total = 'El importe total debe ser mayor que 0';
    }

    if (formData.impuestos_total === '' || formData.impuestos_total === null || formData.impuestos_total === undefined) {
      newErrors.impuestos_total = 'Los impuestos son obligatorios';
    } else {
      const impuestos = parseFloat(formData.impuestos_total) || 0;
      const total = parseFloat(formData.importe_total) || 0;
      
      if (impuestos < 0) {
        newErrors.impuestos_total = 'Los impuestos no pueden ser negativos';
      } else if (impuestos > total) {
        newErrors.impuestos_total = `Los impuestos no pueden ser mayores que el total (${total.toFixed(2)})`;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSubmitError(null);

    try {
      const facturaData = {
        drive_file_name: invoice.nombre || invoice.drive_file_name,
        proveedor_text: formData.proveedor_text.trim(),
        fecha_emision: formData.fecha_emision,
        importe_total: parseFloat(formData.importe_total),
        impuestos_total: parseFloat(formData.impuestos_total),
        numero_factura: formData.numero_factura.trim() || null,
        // base_imponible se calcula automáticamente en backend: importe_total - impuestos_total
        // iva_porcentaje se calcula automáticamente en backend
        // moneda siempre será EUR, no se envía
      };

      const response = await createManualInvoice(facturaData);

      if (response.success) {
        onSuccess(response);
        onClose();
      } else {
        setSubmitError(response.message || 'Error al guardar la factura');
      }
    } catch (error) {
      console.error('Error al guardar factura:', error);
      setSubmitError(
        error.response?.data?.detail ||
        error.message ||
        'Error al guardar la factura. Por favor, intenta nuevamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (!invoice) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: '16px',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
        },
      }}
    >
      <DialogTitle
        sx={{
          backgroundColor: '#475569', // slate-600 (como el sidebar)
          color: '#ffffff',
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FileText size={24} />
          <Typography variant="h6" component="span" sx={{ fontWeight: 700 }}>
            Editar Factura Manualmente
          </Typography>
        </Box>
        <Button
          onClick={onClose}
          sx={{
            minWidth: 'auto',
            padding: '4px',
            color: '#ffffff',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          <X size={20} />
        </Button>
      </DialogTitle>

      <DialogContent sx={{ padding: '24px' }}>
        {/* Información de la factura */}
        <Box sx={{ mb: 3, p: 2, backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
          <Typography variant="body2" sx={{ color: '#6b7280', mb: 1 }}>
            Archivo:
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 600, color: '#1f2937' }}>
            {invoice.nombre || invoice.drive_file_name}
          </Typography>
          {invoice.razon && (
            <>
              <Typography variant="body2" sx={{ color: '#6b7280', mt: 1, mb: 0.5 }}>
                Motivo del error:
              </Typography>
              <Typography variant="body2" sx={{ color: '#dc2626', fontStyle: 'italic' }}>
                {invoice.razon}
              </Typography>
            </>
          )}
        </Box>

        {/* Error general */}
        {submitError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {submitError}
          </Alert>
        )}

        {/* Formulario */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Proveedor con autocompletado */}
          <Autocomplete
            freeSolo
            options={proveedoresOptions}
            getOptionLabel={(option) => {
              if (typeof option === 'string') return option;
              return option.nombre || '';
            }}
            inputValue={formData.proveedor_text}
            onInputChange={(event, newValue, reason) => {
              console.log('🔤 onInputChange:', { newValue, reason, event: event?.type });
              
              // Actualizar el valor del input siempre
              setFormData(prev => ({ ...prev, proveedor_text: newValue || '' }));
              
              // Limpiar errores
              if (errors.proveedor_text) {
                setErrors(prev => {
                  const newErrors = { ...prev };
                  delete newErrors.proveedor_text;
                  return newErrors;
                });
              }
            }}
            onChange={(event, newValue, reason) => {
              console.log('✅ onChange:', { newValue, reason });
              
              // Cuando se selecciona una opción del dropdown
              if (newValue && typeof newValue === 'object' && newValue.nombre) {
                setFormData(prev => ({ ...prev, proveedor_text: newValue.nombre }));
              } else if (typeof newValue === 'string') {
                // Si el usuario escribe libremente
                setFormData(prev => ({ ...prev, proveedor_text: newValue }));
              } else if (newValue === null) {
                // Si se limpia el campo
                setFormData(prev => ({ ...prev, proveedor_text: '' }));
              }
            }}
            loading={proveedorLoading}
            filterOptions={(options, params) => {
              // No filtrar en el cliente, usar los resultados del servidor
              console.log('🔍 filterOptions:', { optionsCount: options.length, inputValue: params.inputValue });
              return options;
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Proveedor *"
                error={!!errors.proveedor_text}
                helperText={errors.proveedor_text || 'Escribe al menos 2 caracteres para buscar proveedores'}
                required
              />
            )}
            renderOption={(props, option) => (
              <Box component="li" {...props} key={option.id || option.nombre}>
                <ListItemText
                  primary={option.nombre}
                  secondary={option.categoria ? `Categoría: ${option.categoria}` : null}
                />
              </Box>
            )}
            noOptionsText={proveedorLoading ? 'Buscando...' : 'No se encontraron proveedores'}
          />

          {/* Fecha de Emisión */}
          <TextField
            label="Fecha de Emisión *"
            type="date"
            value={formData.fecha_emision}
            onChange={handleChange('fecha_emision')}
            error={!!errors.fecha_emision}
            helperText={errors.fecha_emision}
            fullWidth
            required
            InputLabelProps={{
              shrink: true,
            }}
          />

          {/* Fila: Impuestos Total e Importe Total */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Impuestos Total *"
              type="number"
              value={formData.impuestos_total}
              onChange={handleChange('impuestos_total')}
              error={!!errors.impuestos_total}
              helperText={errors.impuestos_total || 'Total de impuestos (IVA, etc.)'}
              fullWidth
              required
              inputProps={{ step: '0.01', min: '0' }}
            />

            <TextField
              label="Importe Total *"
              type="number"
              value={formData.importe_total}
              onChange={handleChange('importe_total')}
              error={!!errors.importe_total}
              helperText={errors.importe_total || 'Total de la factura (incluye impuestos)'}
              fullWidth
              required
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Box>
          
          {/* Información calculada automáticamente */}
          {formData.importe_total && formData.impuestos_total && (
            <Box sx={{ p: 2, backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
              <Typography variant="body2" sx={{ color: '#6b7280', mb: 0.5 }}>
                Calculado automáticamente:
              </Typography>
              <Typography variant="body2" sx={{ color: '#1f2937' }}>
                Base Imponible: €{((parseFloat(formData.importe_total) || 0) - (parseFloat(formData.impuestos_total) || 0)).toFixed(2)}
                {((parseFloat(formData.importe_total) || 0) - (parseFloat(formData.impuestos_total) || 0)) > 0 && (
                  <span style={{ marginLeft: '16px', color: '#6b7280' }}>
                    IVA: {(((parseFloat(formData.impuestos_total) || 0) / ((parseFloat(formData.importe_total) || 0) - (parseFloat(formData.impuestos_total) || 0))) * 100).toFixed(2)}%
                  </span>
                )}
              </Typography>
            </Box>
          )}

          {/* Número de Factura (opcional) */}
          <TextField
            label="Número de Factura"
            value={formData.numero_factura}
            onChange={handleChange('numero_factura')}
            fullWidth
            helperText="Opcional - Moneda siempre será EUR"
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ padding: '16px 24px', borderTop: '1px solid #e5e7eb' }}>
        <Button
          onClick={onClose}
          disabled={loading}
          sx={{ color: '#6b7280' }}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading || Object.keys(errors).length > 0}
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <Save size={16} />}
          sx={{
            backgroundColor: '#475569', // slate-600 (como el sidebar)
            '&:hover': {
              backgroundColor: '#334155', // slate-700 (hover)
            },
          }}
        >
          {loading ? 'Guardando...' : 'Guardar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

