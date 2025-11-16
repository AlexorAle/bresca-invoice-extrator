/**
 * Panel de Carga de Datos - React-admin
 * Migrado desde sección "Carga de Datos" del Dashboard original
 */
import React from 'react';
import { Box } from '@mui/material';

export const CargaDatosPanel = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#ffffff',
        padding: 0,
        margin: 0,
      }}
    >
      <div className="p-2 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
          <div className="bg-white rounded-2xl shadow-header p-6 sm:p-8">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              Carga de Datos
            </h2>
            <p className="text-gray-600">
              Sección de carga de datos en desarrollo...
            </p>
          </div>
        </div>
      </div>
    </Box>
  );
};
