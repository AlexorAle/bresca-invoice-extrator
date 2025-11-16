# Guía para Probar Cambios Localmente - iPad

**Fecha:** 2025-11-12

---

## 🚀 Pasos para Probar Localmente

### 1. Instalar Dependencias (si es necesario)

```bash
cd /home/alex/proyectos/invoice-extractor/frontend
npm install
```

**Nota:** Si ya tienes `node_modules`, puedes saltar este paso.

---

### 2. Iniciar Servidor de Desarrollo

```bash
cd /home/alex/proyectos/invoice-extractor/frontend
npm run dev
```

**Salida esperada:**
```
  VITE v7.1.7  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**El servidor estará disponible en:** `http://localhost:5173/`

---

### 3. Abrir en el Navegador

1. Abre Chrome o Firefox
2. Ve a: `http://localhost:5173/`
3. Deberías ver el dashboard

---

### 4. Emular iPad con DevTools

#### En Chrome:

1. **Abrir DevTools:**
   - Presiona `F12` o `Ctrl+Shift+I` (Linux/Windows)
   - O `Cmd+Option+I` (Mac)

2. **Activar modo dispositivo:**
   - Presiona `Ctrl+Shift+M` (Linux/Windows)
   - O `Cmd+Shift+M` (Mac)
   - O haz clic en el ícono de dispositivo móvil (📱) en la barra de herramientas

3. **Seleccionar iPad:**
   - En el dropdown de dispositivos, selecciona:
     - **iPad Air** (1024x768)
     - **iPad Pro 12.9"** (1366x1024)
     - O crea un dispositivo custom con 1024x768

4. **Verificar cambios:**
   - Deberías ver:
     - ✅ KPIGrid con 2 columnas (no 4)
     - ✅ Más padding en tabla y contenedor
     - ✅ Header con scroll horizontal si los botones no caben
     - ✅ Mejor espaciado general

---

### 5. Probar Diferentes Tamaños

#### Breakpoints a probar:

| Dispositivo | Ancho | Breakpoint | Qué verificar |
|-------------|-------|------------|---------------|
| **Mobile** | 375px | `sm` | 1 columna KPI, padding mínimo |
| **Tablet** | 768px | `md` | 2 columnas KPI, padding medio |
| **iPad** | 1024px | `ipad` | 2 columnas KPI, padding aumentado, scroll en header |
| **Desktop** | 1280px | `lg` | 4 columnas KPI, padding máximo |

#### Cómo cambiar tamaño en DevTools:

1. En modo dispositivo, haz clic en el tamaño actual (ej: "1024 x 768")
2. Escribe un ancho específico o selecciona un dispositivo
3. Observa cómo cambia el layout

---

### 6. Verificar Cambios Específicos

#### ✅ Checklist de Verificación:

- [ ] **KPIGrid:** En iPad (1024px) muestra 2 columnas, no 4
- [ ] **Tabla:** Padding aumentado (celdas más espaciadas)
- [ ] **Contenedor:** Padding aumentado (más espacio lateral)
- [ ] **Header:** Botones de mes pueden hacer scroll si no caben
- [ ] **Desktop (≥1280px):** Sigue mostrando 4 columnas en KPIGrid
- [ ] **Mobile (< 640px):** Sigue funcionando correctamente

---

### 7. Inspeccionar Estilos

#### Ver clases aplicadas:

1. En DevTools, selecciona un elemento (ej: KPIGrid)
2. En la pestaña "Elements" o "Inspector", verás las clases:
   ```html
   <div class="grid grid-cols-1 sm:grid-cols-2 ipad:grid-cols-2 lg:grid-cols-4">
   ```

3. En la pestaña "Computed" o "Estilos calculados", verás los estilos finales aplicados

#### Verificar breakpoint activo:

1. En DevTools, abre la consola (`Console`)
2. Ejecuta:
   ```javascript
   window.matchMedia('(min-width: 1024px)').matches
   ```
   - `true` = breakpoint `ipad` está activo
   - `false` = breakpoint `ipad` no está activo

---

### 8. Probar con Diferentes Datos

#### Si el backend está corriendo:

1. El dashboard debería cargar datos automáticamente
2. Verifica que la tabla se vea bien con datos reales
3. Prueba cambiar de mes/año y verificar que el layout se mantiene

#### Si el backend NO está corriendo:

1. Verás un error de conexión
2. Esto es normal, pero puedes verificar el layout igual
3. O inicia el backend también (si lo necesitas)

---

## 🔧 Troubleshooting

### Problema: "npm run dev" no funciona

**Solución:**
```bash
# Verificar que estás en el directorio correcto
cd /home/alex/proyectos/invoice-extractor/frontend

# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install

# Intentar de nuevo
npm run dev
```

### Problema: Cambios no se reflejan

**Solución:**
- Vite tiene hot-reload, los cambios deberían aparecer automáticamente
- Si no, recarga la página (`Ctrl+R` o `Cmd+R`)
- O reinicia el servidor (`Ctrl+C` y luego `npm run dev`)

### Problema: No veo el breakpoint `ipad` funcionando

**Solución:**
1. Verifica que `tailwind.config.js` tiene el breakpoint configurado
2. Verifica que el ancho de viewport es exactamente 1024px o más
3. En DevTools, asegúrate de que el zoom está al 100%

---

## 📊 Comparación Visual

### Antes (sin breakpoint iPad):
- iPad (1024px) → 4 columnas KPI (muy estrechas)
- Padding tabla: 16px
- Header sin scroll

### Después (con breakpoint iPad):
- iPad (1024px) → 2 columnas KPI (cómodas)
- Padding tabla: 32px
- Header con scroll si es necesario

---

## 🎯 Comandos Rápidos

```bash
# 1. Ir al directorio frontend
cd /home/alex/proyectos/invoice-extractor/frontend

# 2. Iniciar servidor de desarrollo
npm run dev

# 3. Abrir en navegador (automático o manual)
# http://localhost:5173/

# 4. Abrir DevTools (F12)
# 5. Activar modo dispositivo (Ctrl+Shift+M)
# 6. Seleccionar iPad Air (1024x768)
```

---

## ✅ Verificación Final

Después de probar, deberías confirmar:

- [ ] El dashboard se ve bien en iPad (1024px)
- [ ] No hay regresiones en desktop (≥1280px)
- [ ] No hay regresiones en mobile (< 640px)
- [ ] Los cambios mejoran la experiencia en iPad

Si todo está bien, puedes proceder con el rebuild y deploy en Docker.

---

**Fin de la guía**


