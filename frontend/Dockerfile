# Dockerfile for Invoice Extractor Frontend (Vite + React)
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

# Production image with Nginx
FROM nginx:alpine AS runner
WORKDIR /usr/share/nginx/html

# Remove default nginx static assets
RUN rm -rf ./*

# Copy built assets
COPY --from=builder /app/dist .

# Copy nginx configuration for SPA routing with base path
# Traefik NO hace stripPrefix según docker-compose, así que nginx recibe /invoice-dashboard/...
# Vite construye con base: /invoice-dashboard/, así que los archivos están en la raíz pero el HTML referencia /invoice-dashboard/...
# Necesitamos servir los assets desde la raíz cuando se piden con el prefijo
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Servir assets estáticos cuando vienen con prefijo /invoice-dashboard/assets/ \
    location ~* ^/invoice-dashboard/assets/(.+)$ { \
        alias /usr/share/nginx/html/assets/$1; \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
        access_log off; \
    } \
    \
    # Servir otros archivos estáticos con prefijo (vite.svg, etc) \
    location ~* ^/invoice-dashboard/([^/]+\\.(svg|ico|png|jpg|jpeg|gif|woff|woff2|ttf|eot))$ { \
        alias /usr/share/nginx/html/$1; \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # Servir index.html para todas las rutas del dashboard (SPA routing) \
    location ~* ^/invoice-dashboard(/.*)?$ { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Redirigir raíz a /invoice-dashboard/ \
    location = / { \
        return 301 /invoice-dashboard/; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

