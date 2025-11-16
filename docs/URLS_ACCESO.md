# URLs de Acceso - Dashboard Invoice Extractor

**Fecha:** 2025-11-12

---

## 🌐 URLs Disponibles

### 1. Desarrollo Local (Vite Dev Server)

**URL:** `http://localhost:5173/invoice-dashboard/`

**Estado:** ✅ Activo

**Características:**
- Hot-reload automático (cambios se reflejan al guardar)
- Ideal para desarrollo y testing
- Solo accesible desde el servidor local

**Nota:** El servidor está corriendo en background. Para detenerlo:
```bash
pkill -f "vite"
```

---

### 2. Producción (Servidor Externo)

**URL:** `http://82.25.101.32/invoice-dashboard/`

**Estado:** ✅ Activo (después de rebuild)

**Características:**
- Accesible desde cualquier lugar
- Build optimizado de producción
- Servido por Traefik + Docker

---

## 🔍 Verificación

### Desarrollo Local:
```bash
curl http://localhost:5173/invoice-dashboard/ | head -20
```

### Producción:
```bash
curl http://82.25.101.32/invoice-dashboard/ | head -20
```

O desde el navegador:
- Local: `http://localhost:5173/invoice-dashboard/`
- Externo: `http://82.25.101.32/invoice-dashboard/`

---

## ⚠️ Nota Importante

**El servidor de desarrollo Vite usa el `base: '/invoice-dashboard/'` configurado en `vite.config.js`**, por eso la URL incluye `/invoice-dashboard/`.

Si quieres probar sin el prefijo, puedes:
1. Cambiar temporalmente `base: '/'` en `vite.config.js`
2. O acceder directamente a `http://localhost:5173/invoice-dashboard/`

---

**Fin del documento**


