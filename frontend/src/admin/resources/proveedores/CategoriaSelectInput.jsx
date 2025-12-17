/**
 * SelectInput de categorías que carga desde la BD
 */
import React from 'react';
import { SelectInput, useGetList } from 'react-admin';

export const CategoriaSelectInput = (props) => {
  const { data, isLoading } = useGetList('categorias', {
    pagination: { page: 1, perPage: 500 },
    sort: { field: 'nombre', order: 'ASC' },
    filter: { activo: true },
  });

  const choices = data?.map(cat => ({
    id: cat.nombre, // Usar nombre como ID para compatibilidad
    name: cat.nombre,
  })) || [];

  return (
    <SelectInput
      {...props}
      source="categoria"
      label="Categoría"
      choices={choices}
      fullWidth
      disabled={isLoading}
      emptyText={isLoading ? 'Cargando categorías...' : 'Sin categorías disponibles'}
    />
  );
};
