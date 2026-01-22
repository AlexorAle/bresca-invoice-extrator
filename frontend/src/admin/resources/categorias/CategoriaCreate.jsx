/**
 * Crear Categoría - React-admin
 */
import React from 'react';
import {
  Create,
  SimpleForm,
  TextInput,
  required,
} from 'react-admin';
import { Box, Typography, Button, TextField } from '@mui/material';
import { Tag, ArrowLeft } from 'lucide-react';
import { SPACING, PAGE_LAYOUT } from '../../styles/designTokens';
import { useNavigate } from 'react-router-dom';

export const CategoriaCreate = (props) => {
  const navigate = useNavigate();
  
  return (
    <Create {...props} title="Crear Categoría">
      <Box
        sx={{
          minHeight: '100vh',
          backgroundColor: '#f9fafb',
          padding: 0,
          margin: 0,
        }}
      >
        <Box sx={{ p: { xs: 1, sm: 2, md: 3, lg: 4 } }}>
          <Box sx={{ mx: 'auto', px: { xs: 1.5, sm: 2, md: 2.5, lg: 3 } }}>
            {/* Título con botón volver */}
            <Box sx={{ 
              mt: PAGE_LAYOUT.titleMarginTop, 
              mb: SPACING.sm,
              display: 'flex', 
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 2,
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Tag size={32} color="#3b82f6" />
                <Typography
                  variant="h3"
                  sx={{
                    fontFamily: "'Inter', 'Outfit', sans-serif",
                    fontWeight: 700,
                    fontSize: '2rem',
                    color: '#1e293b',
                    margin: 0,
                  }}
                >
                  Crear Nueva Categoría
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<ArrowLeft size={18} />}
                onClick={() => navigate('/datos')}
                sx={{
                  borderColor: '#64748b',
                  color: '#64748b',
                  '&:hover': {
                    borderColor: '#475569',
                    backgroundColor: '#f1f5f9',
                  },
                }}
              >
                Volver
              </Button>
            </Box>

            {/* Formulario */}
            <Box
              sx={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
                padding: SPACING.lg,
                maxWidth: '600px',
              }}
            >
              <SimpleForm>
                <TextInput 
                  source="nombre" 
                  label="Nombre de la Categoría" 
                  fullWidth
                  validate={required()}
                  sx={{ mb: 3 }}
                />
                <TextInput 
                  source="descripcion" 
                  label="Descripción (opcional)" 
                  fullWidth
                  multiline
                  rows={3}
                  sx={{ mb: 3 }}
                />
                <TextInput 
                  source="color" 
                  label="Color (hex)" 
                  placeholder="#3b82f6"
                  defaultValue="#3b82f6"
                  sx={{ mb: 3 }}
                  helperText="Color hexadecimal para identificar visualmente la categoría (ej: #3b82f6)"
                />
              </SimpleForm>
            </Box>
          </Box>
        </Box>
      </Box>
    </Create>
  );
};
