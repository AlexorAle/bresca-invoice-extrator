/**
 * Componente Modal para edición manual de facturas pendientes
 */
import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import { X, Save, FileText } from 'lucide-react';
import { createManualInvoice } from '../utils/api';

export const ManualInvoiceForm = ({ open, onClose, invoice, onSuccess }) => {
  const [formData, setFormData] = useState({
    proveedor_text: '',
    fecha_emision: '',
    importe_total: '',
    base_imponible: '',
    impuestos_total: '',
    iva_porcentaje: '',
    numero_factura: '',
    moneda: 'EUR',
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

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
        base_imponible: invoice.base_imponible || '',
        impuestos_total: invoice.impuestos_total || '',
        iva_porcentaje: invoice.iva_porcentaje || '',
        numero_factura: invoice.numero_factura || '',
        moneda: invoice.moneda || 'EUR',
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

  // Calcular IVA automáticamente si cambian base o impuestos
  useEffect(() => {
    if (formData.base_imponible && formData.impuestos_total) {
      const base = parseFloat(formData.base_imponible) || 0;
      const impuestos = parseFloat(formData.impuestos_total) || 0;
      if (base > 0) {
        const ivaCalculado = ((impuestos / base) * 100).toFixed(2);
        setFormData(prev => ({
          ...prev,
          iva_porcentaje: ivaCalculado,
        }));
      }
    }
  }, [formData.base_imponible, formData.impuestos_total]);

  // Validar importe total = base + impuestos
  useEffect(() => {
    if (formData.base_imponible && formData.impuestos_total && formData.importe_total) {
      const base = parseFloat(formData.base_imponible) || 0;
      const impuestos = parseFloat(formData.impuestos_total) || 0;
      const total = parseFloat(formData.importe_total) || 0;
      const expectedTotal = base + impuestos;
      const diferencia = Math.abs(total - expectedTotal);

      if (diferencia > 0.01) {
        setErrors(prev => ({
          ...prev,
          importe_total: `El total debe ser ${expectedTotal.toFixed(2)} (base + impuestos)`,
        }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.importe_total;
          return newErrors;
        });
      }
    }
  }, [formData.base_imponible, formData.impuestos_total, formData.importe_total]);

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

    if (!formData.proveedor_text.trim()) {
      newErrors.proveedor_text = 'El proveedor es obligatorio';
    }

    if (!formData.fecha_emision) {
      newErrors.fecha_emision = 'La fecha de emisión es obligatoria';
    }

    if (!formData.importe_total || parseFloat(formData.importe_total) <= 0) {
      newErrors.importe_total = 'El importe total debe ser mayor que 0';
    }

    if (!formData.base_imponible || parseFloat(formData.base_imponible) <= 0) {
      newErrors.base_imponible = 'La base imponible debe ser mayor que 0';
    }

    if (!formData.impuestos_total || parseFloat(formData.impuestos_total) < 0) {
      newErrors.impuestos_total = 'Los impuestos no pueden ser negativos';
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
        base_imponible: parseFloat(formData.base_imponible),
        impuestos_total: parseFloat(formData.impuestos_total),
        iva_porcentaje: formData.iva_porcentaje ? parseFloat(formData.iva_porcentaje) : null,
        numero_factura: formData.numero_factura.trim() || null,
        moneda: formData.moneda,
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
          {/* Proveedor */}
          <TextField
            label="Proveedor *"
            value={formData.proveedor_text}
            onChange={handleChange('proveedor_text')}
            error={!!errors.proveedor_text}
            helperText={errors.proveedor_text}
            fullWidth
            required
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

          {/* Fila: Base Imponible y Impuestos */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Base Imponible *"
              type="number"
              value={formData.base_imponible}
              onChange={handleChange('base_imponible')}
              error={!!errors.base_imponible}
              helperText={errors.base_imponible}
              fullWidth
              required
              inputProps={{ step: '0.01', min: '0' }}
            />

            <TextField
              label="Impuestos Total *"
              type="number"
              value={formData.impuestos_total}
              onChange={handleChange('impuestos_total')}
              error={!!errors.impuestos_total}
              helperText={errors.impuestos_total}
              fullWidth
              required
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Box>

          {/* Fila: Importe Total e IVA % */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Importe Total *"
              type="number"
              value={formData.importe_total}
              onChange={handleChange('importe_total')}
              error={!!errors.importe_total}
              helperText={errors.importe_total || 'Debe ser igual a Base + Impuestos'}
              fullWidth
              required
              inputProps={{ step: '0.01', min: '0' }}
            />

            <TextField
              label="IVA %"
              type="number"
              value={formData.iva_porcentaje}
              onChange={handleChange('iva_porcentaje')}
              fullWidth
              inputProps={{ step: '0.01', min: '0', max: '100' }}
              helperText="Se calcula automáticamente"
            />
          </Box>

          {/* Fila: Número de Factura y Moneda */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Número de Factura"
              value={formData.numero_factura}
              onChange={handleChange('numero_factura')}
              fullWidth
            />

            <TextField
              label="Moneda"
              value={formData.moneda}
              onChange={handleChange('moneda')}
              fullWidth
              select
              SelectProps={{
                native: true,
              }}
            >
              <option value="EUR">EUR</option>
              <option value="USD">USD</option>
              <option value="GBP">GBP</option>
            </TextField>
          </Box>
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

