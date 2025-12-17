/**
 * LoginPage - Página de autenticación con Google Sign-In
 * Usa @react-oauth/google para autenticación OAuth2
 */
import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';
import { COLORS, BORDER_RADIUS, SPACING } from '../admin/styles/designTokens';

export function LoginPage({ onLoginSuccess, loading = false }) {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // Enviar el ID token al backend
      const response = await fetch('/invoice-api/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Importante: incluir cookies
        body: JSON.stringify({
          token: credentialResponse.credential,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al autenticar con Google');
      }

      const data = await response.json();
      
      // Llamar callback de éxito
      if (onLoginSuccess) {
        onLoginSuccess(data);
      }
    } catch (error) {
      console.error('Error en autenticación:', error);
      alert(`Error al autenticar: ${error.message}`);
    }
  };

  const handleGoogleError = () => {
    console.error('Error en Google Sign-In');
    alert('Error al iniciar sesión con Google. Por favor, intenta nuevamente.');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: COLORS.background.subtle,
        padding: SPACING.lg,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          padding: SPACING['2xl'],
          borderRadius: BORDER_RADIUS.xl,
          maxWidth: '400px',
          width: '100%',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontWeight: 700,
            color: COLORS.text.primary,
            marginBottom: SPACING.md,
          }}
        >
          Invoice Dashboard
        </Typography>
        
        <Typography
          variant="body1"
          sx={{
            color: COLORS.text.secondary,
            marginBottom: SPACING.xl,
          }}
        >
          Inicia sesión para acceder al dashboard
        </Typography>

        {loading ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: SPACING.md,
            }}
          >
            <CircularProgress size={40} />
            <Typography variant="body2" sx={{ color: COLORS.text.secondary }}>
              Verificando credenciales...
            </Typography>
          </Box>
        ) : (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              '& > div': {
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
              },
            }}
          >
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              useOneTap={true}
              theme="filled_blue"
              size="large"
              text="continue_with"
              width="100%"
            />
          </Box>
        )}
      </Paper>
    </Box>
  );
}
