/**
 * FacturasTable - Componente de tabla migrado completamente a MUI
 * Reemplazo de FacturasTable.jsx legacy (Tailwind + HTML table)
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Typography,
  IconButton,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import { ChevronUp, ChevronDown, Edit, FileText } from 'lucide-react';
import { sanitizeErrorMessage } from '../../utils/api';
import { ManualInvoiceForm } from '../ManualInvoiceForm';
import { BaseCard } from './BaseCard';
import { COLORS, BORDER_RADIUS, TABLE_STYLES } from '../../admin/styles/designTokens';

export function FacturasTable({ 
  facturas = [], 
  failedInvoices = [], 
  loading = false, 
  showTabs = true, 
  showOnlyPendientes = false, 
  onRefresh 
}) {
  const [activeTab, setActiveTab] = useState('todas');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(amount);
  };


  // Función para ordenar
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Ordenar facturas
  const sortedFacturas = useMemo(() => {
    if (!sortConfig.key) return facturas;
    
    return [...facturas].sort((a, b) => {
      let aValue, bValue;
      
      if (sortConfig.key === 'fecha') {
        aValue = a.fecha_emision ? new Date(a.fecha_emision).getTime() : 0;
        bValue = b.fecha_emision ? new Date(b.fecha_emision).getTime() : 0;
      } else if (sortConfig.key === 'impuestos') {
        aValue = parseFloat(a.impuestos_total || 0);
        bValue = parseFloat(b.impuestos_total || 0);
      } else if (sortConfig.key === 'total') {
        aValue = parseFloat(a.importe_total || 0);
        bValue = parseFloat(b.importe_total || 0);
      } else {
        return 0;
      }
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [facturas, sortConfig]);

  // Sanitizar las razones de las facturas pendientes
  const facturasPendientes = useMemo(() => {
    const sanitized = (failedInvoices || []).map(invoice => {
      const originalRazon = invoice.razon ? String(invoice.razon) : '';
      const sanitizedRazon = originalRazon ? sanitizeErrorMessage(originalRazon) : '';
      
      return {
        ...invoice,
        razon: sanitizedRazon || 'Sin razón especificada'
      };
    });
    return sanitized;
  }, [failedInvoices]);

  // Renderizar botón de ordenamiento
  const SortButton = ({ columnKey, children }) => {
    const isActive = sortConfig.key === columnKey;
    return (
      <Box
        onClick={() => handleSort(columnKey)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 0.5,
          cursor: 'pointer',
          color: COLORS.text.primary,
          '&:hover': {
            color: COLORS.primary.main,
          },
        }}
      >
        {children}
        {isActive ? (
          sortConfig.direction === 'asc' ? (
            <ChevronUp size={16} color={COLORS.primary.main} />
          ) : (
            <ChevronDown size={16} color={COLORS.primary.main} />
          )
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            <ChevronUp size={8} color={COLORS.text.secondary} style={{ opacity: 0.5 }} />
            <ChevronDown size={8} color={COLORS.text.secondary} style={{ opacity: 0.5, marginTop: -4 }} />
          </Box>
        )}
      </Box>
    );
  };

  if (loading) {
    return (
      <BaseCard>
        <Box>
          <Skeleton variant="text" width="25%" height={24} sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Skeleton variant="rectangular" height={48} />
            <Skeleton variant="rectangular" height={48} />
            <Skeleton variant="rectangular" height={48} />
          </Box>
        </Box>
      </BaseCard>
    );
  }

  return (
    <BaseCard>
      {/* Tabs - Solo mostrar si showTabs es true y no es solo pendientes */}
      {showTabs && !showOnlyPendientes && (
        <Box sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: { xs: '16px', sm: '18px' },
                fontWeight: 500,
                minHeight: '48px',
              },
              '& .Mui-selected': {
                color: '#9333ea',
              },
            }}
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab label={`Todas (${facturas.length})`} value="todas" />
            <Tab label={`Pendientes (${facturasPendientes.length})`} value="pendientes" />
          </Tabs>
        </Box>
      )}

      {/* Tabla de facturas */}
      <TableContainer>
        <Table>
          {showOnlyPendientes ? (
            // Tabla de pendientes
            <>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    FACTURA
                  </TableCell>
                  <TableCell align="center" sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    ESTADO
                  </TableCell>
                  <TableCell sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    RAZÓN
                  </TableCell>
                  <TableCell align="center" sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    ACCIONES
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {facturasPendientes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                      <Typography sx={{ color: COLORS.text.secondary, fontSize: '18px' }}>
                        No hay facturas pendientes de revisión
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  facturasPendientes.map((invoice, index) => {
                    return (
                      <TableRow
                        key={index}
                        sx={{
                          '&:hover': {
                            backgroundColor: 'rgba(37, 99, 235, 0.04)',
                          },
                        }}
                      >
                        <TableCell sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                          fontSize: TABLE_STYLES.cellFontSize,
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <FileText size={20} color={COLORS.text.secondary} />
                            <Typography sx={{ 
                              fontWeight: 500, 
                              color: COLORS.text.primary,
                              wordBreak: 'break-word',
                            }}>
                              {invoice.nombre}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                          fontSize: TABLE_STYLES.cellFontSize,
                          color: COLORS.text.secondary,
                          wordBreak: 'break-word',
                        }}>
                          {invoice.razon || 'Sin razón especificada'}
                        </TableCell>
                        <TableCell align="center" sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                        }}>
                          <IconButton
                            onClick={() => {
                              setSelectedInvoice(invoice);
                              setIsEditModalOpen(true);
                            }}
                            size="small"
                            sx={{
                              color: COLORS.text.secondary,
                              '&:hover': {
                                color: COLORS.text.primary,
                                backgroundColor: COLORS.background.subtle,
                              },
                            }}
                            title="Editar factura manualmente"
                          >
                            <Edit size={18} />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </>
          ) : activeTab === 'todas' ? (
            // Tabla de todas las facturas
            <>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    PROVEEDOR
                  </TableCell>
                  <TableCell align="center" sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    <SortButton columnKey="fecha">FECHA</SortButton>
                  </TableCell>
                  <TableCell align="center" sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    <SortButton columnKey="total">TOTAL</SortButton>
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {!facturas || facturas.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                      <Typography sx={{ color: COLORS.text.secondary, fontSize: '18px' }}>
                        No hay facturas para mostrar
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sortedFacturas.map((factura) => (
                    <TableRow
                      key={factura.id}
                      sx={{
                        '&:hover': {
                          backgroundColor: 'rgba(37, 99, 235, 0.04)',
                          '& td': {
                            color: COLORS.primary.main,
                          },
                        },
                      }}
                    >
                      <TableCell sx={{ 
                        py: 2.5,
                        px: { xs: 2.5, md: 3.5, lg: 4.5 },
                        fontSize: TABLE_STYLES.cellFontSize,
                        fontWeight: 500,
                        color: COLORS.text.primary,
                      }}>
                        {factura.proveedor_nombre || 'N/A'}
                      </TableCell>
                      <TableCell align="center" sx={{ 
                        py: 2.5,
                        px: { xs: 2.5, md: 3.5, lg: 4.5 },
                        fontSize: TABLE_STYLES.cellFontSize,
                        color: COLORS.text.primary,
                        whiteSpace: 'nowrap',
                      }}>
                        {formatDate(factura.fecha_emision)}
                      </TableCell>
                      <TableCell align="center" sx={{ 
                        py: 2.5,
                        px: { xs: 2.5, md: 3.5, lg: 4.5 },
                        fontSize: TABLE_STYLES.cellFontSize,
                        fontWeight: 600,
                        color: COLORS.text.primary,
                        whiteSpace: 'nowrap',
                      }}>
                        {formatCurrency(factura.importe_total || 0)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </>
          ) : (
            // Tab pendientes dentro de tabs
            <>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    FACTURA
                  </TableCell>
                  <TableCell sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    RAZÓN
                  </TableCell>
                  <TableCell align="center" sx={{ 
                    fontSize: TABLE_STYLES.headerFontSize,
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    py: 2.5,
                    px: { xs: 2.5, md: 3.5, lg: 4.5 },
                  }}>
                    ACCIONES
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {facturasPendientes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                      <Typography sx={{ color: COLORS.text.secondary, fontSize: '18px' }}>
                        No hay facturas pendientes de revisión
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  facturasPendientes.map((invoice, index) => {
                    return (
                      <TableRow
                        key={index}
                        sx={{
                          '&:hover': {
                            backgroundColor: 'rgba(37, 99, 235, 0.04)',
                            '& td': {
                              color: COLORS.primary.main,
                            },
                          },
                        }}
                      >
                        <TableCell sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                          fontSize: TABLE_STYLES.cellFontSize,
                          fontWeight: 500,
                          color: COLORS.text.primary,
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                            <FileText size={20} color={COLORS.text.secondary} />
                            <Typography sx={{ wordBreak: 'break-word' }}>
                              {invoice.nombre}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                          fontSize: TABLE_STYLES.cellFontSize,
                          color: COLORS.text.secondary,
                          wordBreak: 'break-word',
                        }}>
                          {invoice.razon || 'Sin razón especificada'}
                        </TableCell>
                        <TableCell align="center" sx={{ 
                          py: 2.5,
                          px: { xs: 2.5, md: 3.5, lg: 4.5 },
                        }}>
                          <IconButton
                            onClick={() => {
                              setSelectedInvoice(invoice);
                              setIsEditModalOpen(true);
                            }}
                            size="small"
                            sx={{
                              color: COLORS.text.secondary,
                              '&:hover': {
                                color: COLORS.text.primary,
                                backgroundColor: COLORS.background.subtle,
                              },
                            }}
                            title="Editar factura manualmente"
                          >
                            <Edit size={18} />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </>
          )}
        </Table>
      </TableContainer>

      {/* Modal de edición */}
      {selectedInvoice && (
        <ManualInvoiceForm
          open={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedInvoice(null);
          }}
          invoice={selectedInvoice}
          onSuccess={() => {
            setIsEditModalOpen(false);
            setSelectedInvoice(null);
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </BaseCard>
  );
}
