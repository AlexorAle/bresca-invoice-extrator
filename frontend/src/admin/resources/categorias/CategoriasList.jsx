/**
 * Lista de Categorías - React-admin
 * Gestión de categorías para proveedores
 */
import React from 'react';
import {
  List,
  Datagrid,
  TextField,
  BooleanField,
  EditButton,
  DeleteButton,
  CreateButton,
  TopToolbar,
  SearchInput,
  Filter,
  DateField,
  useGetList,
  useDelete,
} from 'react-admin';
import { Box, Typography, CircularProgress, Button as MuiButton } from '@mui/material';
import { Tag, Plus, Edit, Trash2 } from 'lucide-react';
import { SPACING, PAGE_LAYOUT } from '../../styles/designTokens';
import { useNavigate } from 'react-router-dom';

const CategoriasFilter = (props) => (
  <Filter {...props}>
    <SearchInput source="nombre" alwaysOn />
  </Filter>
);

const CategoriasListActions = () => (
  <TopToolbar>
    <CreateButton />
  </TopToolbar>
);

export const CategoriasList = (props) => {
  // Si se usa como componente dentro de otro (sin List wrapper), renderizar solo el contenido
  const isEmbedded = props.embedded === true;
  const navigate = useNavigate();
  
  // Obtener categorías usando el dataProvider
  const { data: categorias, isLoading, refetch } = useGetList('categorias', {
    pagination: { page: 1, perPage: 500 },
    sort: { field: 'nombre', order: 'ASC' },
    filter: { activo: true },
  });

  const [deleteOne] = useDelete();

  const handleCreate = () => {
    navigate('/categorias/create');
  };

  const handleEdit = (id) => {
    navigate(`/categorias/${id}`);
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta categoría?')) {
      try {
        await deleteOne('categorias', { id });
        refetch();
      } catch (error) {
        console.error('Error al eliminar categoría:', error);
        alert('Error al eliminar categoría');
      }
    }
  };
  
  const content = (
    <Box
      sx={{
        minHeight: isEmbedded ? 'auto' : '100vh',
        backgroundColor: isEmbedded ? 'transparent' : '#f9fafb',
        padding: 0,
        margin: 0,
      }}
    >
      <Box sx={isEmbedded ? {} : { p: { xs: 2, sm: 4, md: 6, lg: 8 } }}>
        <Box sx={isEmbedded ? {} : { mx: 'auto', px: { xs: 3, sm: 4, md: 5, lg: 6 } }}>
          {!isEmbedded && (
            <>
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
                  Categorías
                </Typography>
              </Box>

              {/* Subtítulo */}
              <Box sx={{ mb: PAGE_LAYOUT.sectionSpacing }}>
                <Typography
                  variant="body1"
                  sx={{
                    fontFamily: "'Inter', 'Outfit', sans-serif",
                    color: '#64748b',
                    fontSize: '1rem',
                  }}
                >
                  Gestiona las categorías disponibles para proveedores y otros usos
                </Typography>
              </Box>
            </>
          )}

          {/* Botón crear (solo si está embebido) */}
          {isEmbedded && (
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <MuiButton
                variant="contained"
                startIcon={<Plus size={18} />}
                onClick={handleCreate}
                sx={{
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: '#2563eb',
                  },
                }}
              >
                Crear Categoría
              </MuiButton>
            </Box>
          )}

          {/* Tabla de categorías */}
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box
              sx={{
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
                overflow: 'hidden',
              }}
            >
              {isEmbedded ? (
                // Tabla simple cuando está embebido
                <Box sx={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>ID</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Color</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Nombre</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Descripción</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Activo</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categorias?.map((cat) => (
                        <tr key={cat.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                          <td style={{ padding: '12px', fontSize: '0.875rem' }}>{cat.id}</td>
                          <td style={{ padding: '12px' }}>
                            <Box
                              component="div"
                              sx={{
                                width: 40,
                                height: 30,
                                borderRadius: '6px',
                                backgroundColor: (cat.color && cat.color !== 'null' && cat.color !== null) ? cat.color : '#3b82f6',
                                border: '2px solid #e5e7eb',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                              }}
                              title={(cat.color && cat.color !== 'null' && cat.color !== null) ? cat.color : '#3b82f6'}
                            />
                          </td>
                          <td style={{ padding: '12px', fontWeight: 500, fontSize: '0.875rem' }}>{cat.nombre}</td>
                          <td style={{ padding: '12px', color: '#64748b', fontSize: '0.875rem' }}>{cat.descripcion || '-'}</td>
                          <td style={{ padding: '12px' }}>
                            <Box
                              component="span"
                              sx={{
                                display: 'inline-block',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                backgroundColor: cat.activo ? '#d1fae5' : '#fee2e2',
                                color: cat.activo ? '#065f46' : '#991b1b',
                              }}
                            >
                              {cat.activo ? 'Sí' : 'No'}
                            </Box>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <MuiButton
                                size="small"
                                onClick={() => handleEdit(cat.id)}
                                sx={{ minWidth: 'auto', p: 0.5 }}
                              >
                                <Edit size={16} color="#3b82f6" />
                              </MuiButton>
                              <MuiButton
                                size="small"
                                onClick={() => handleDelete(cat.id)}
                                sx={{ minWidth: 'auto', p: 0.5, color: '#ef4444' }}
                              >
                                <Trash2 size={16} />
                              </MuiButton>
                            </Box>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {(!categorias || categorias.length === 0) && (
                    <Box sx={{ p: 4, textAlign: 'center', color: '#64748b' }}>
                      No hay categorías disponibles
                    </Box>
                  )}
                </Box>
              ) : (
                <Datagrid>
                  <TextField source="id" label="ID" />
                  <TextField source="nombre" label="Nombre" />
                  <TextField source="descripcion" label="Descripción" />
                  <BooleanField source="activo" label="Activo" />
                  <DateField source="creado_en" label="Creado" showTime />
                  <DateField source="actualizado_en" label="Actualizado" showTime />
                  <EditButton />
                  <DeleteButton />
                </Datagrid>
              )}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );

  if (isEmbedded) {
    return content;
  }

  return (
    <List
      {...props}
      title="Categorías"
      filters={<CategoriasFilter />}
      actions={<CategoriasListActions />}
      empty={false}
    >
      {content}
    </List>
  );
};
