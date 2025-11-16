# Dockerfile for Invoice Extractor Frontend (Vite + React)
# ✅ Sin Nginx - usando servidor HTTP simple (serve)
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Build the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments for environment variables
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build Vite
RUN npm run build

# Production image with serve (servidor HTTP simple, sin Nginx)
FROM base AS runner
WORKDIR /app

# Instalar serve globalmente
RUN npm install -g serve

# Copiar archivos construidos
COPY --from=builder /app/dist ./dist

# Exponer puerto 80 (serve puede usar cualquier puerto)
EXPOSE 80

# Usar serve para servir los archivos estáticos
# -s: SPA mode (servir index.html para todas las rutas)
# -l: puerto a escuchar
# -n: no mostrar banner
CMD ["serve", "-s", "dist", "-l", "80", "-n"]
