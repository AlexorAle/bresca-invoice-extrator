/**
 * Crear Categoría - React-admin
 */
import React from 'react';
import {
  Create,
  SimpleForm,
  TextInput,
  required,
  TopToolbar,
} from 'react-admin';
import { Box, Typography, Button, TextField } from '@mui/material';
import { Tag, ArrowLeft } from 'lucide-react';
import { SPACING, PAGE_LAYOUT } from '../../styles/designTokens';
import { useNavigate } from 'react-router-dom';

const CreateActions = () => {
  const navigate = useNavigate();
  
  return (
    <TopToolbar>
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
    </TopToolbar>
  );
};

export const CategoriaCreate = (props) => {
  return (
    <Create {...props} title="Crear Categoría" actions={<CreateActions />}>
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
            {/* Título */}
            <Box sx={{ 
              mt: PAGE_LAYOUT.titleMarginTop, 
              mb: SPACING.sm,
              display: 'flex', 
              alignItems: 'center',
              gap: 2,
            }}>
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
          </div>
        </div>
      </Box>
    </Create>
  );
};
