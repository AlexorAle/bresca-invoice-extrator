# Guía de Descarga de Documentos

**Ubicación en servidor:** `~/proyectos/docs/`  
**Servidor:** 82.25.101.32  
**Usuario:** alex

---

## 📥 Opción 1: PowerShell (Windows) - Recomendado

### Requisitos
- Windows 10/11 (OpenSSH viene preinstalado)
- O instalar OpenSSH si no está disponible

### Comando Completo

```powershell
# Crear carpeta local para los documentos
New-Item -ItemType Directory -Force -Path ".\documentos-servidor"

# Descargar todos los documentos
scp -r alex@82.25.101.32:/home/alex/proyectos/docs/*.md .\documentos-servidor\
```

### Comando Simplificado (una línea)

```powershell
scp alex@82.25.101.32:/home/alex/proyectos/docs/*.md .
```

**Nota:** Esto descargará los archivos en el directorio actual de PowerShell.

---

## 📥 Opción 2: SSH + SCP (Cualquier SO)

### Desde terminal SSH/Linux/Mac

```bash
# Crear carpeta local
mkdir -p ~/documentos-servidor

# Descargar todos los documentos
scp alex@82.25.101.32:/home/alex/proyectos/docs/*.md ~/documentos-servidor/
```

### Con rsync (si está disponible - más eficiente)

```bash
rsync -avz alex@82.25.101.32:/home/alex/proyectos/docs/*.md ~/documentos-servidor/
```

---

## 📥 Opción 3: PowerShell con WinSCP (GUI)

Si prefieres una interfaz gráfica:

1. Descargar WinSCP: https://winscp.net/
2. Conectar a: `alex@82.25.101.32`
3. Navegar a: `/home/alex/proyectos/docs/`
4. Seleccionar todos los `.md` y descargar

---

## 📋 Documentos a Descargar

1. `SERVER_ARCHITECTURE_OVERVIEW.md` (37KB)
2. `MAPA_PUERTOS.md` (5.6KB)
3. `LOKI_INTEGRATION.md` (4.7KB)
4. `COMMAND_CENTER_DASHBOARD.md` (5.0KB)
5. `INDICE_DOCUMENTACION.md` (6.1KB)
6. `LIMPIEZA_DISCO_ACCIONES.md` (15KB)

**Total:** ~74KB

---

## 🔐 Autenticación

### Si usas clave SSH (recomendado)

```powershell
# PowerShell
scp -i C:\ruta\a\tu\clave_privada alex@82.25.101.32:/home/alex/proyectos/docs/*.md .
```

### Si usas contraseña

El comando te pedirá la contraseña cuando lo ejecutes.

---

## ✅ Verificación

Después de descargar, verifica que tienes los 6 archivos:

```powershell
# PowerShell
Get-ChildItem *.md | Select-Object Name, Length
```

```bash
# Linux/Mac
ls -lh *.md
```

---

## 🚀 Comando Rápido (PowerShell - Copiar y Pegar)

```powershell
scp alex@82.25.101.32:/home/alex/proyectos/docs/*.md .
```

Este comando:
- ✅ Descarga todos los `.md` de `~/proyectos/docs/`
- ✅ Los guarda en el directorio actual
- ✅ Te pedirá la contraseña (o usará tu clave SSH si está configurada)

---

**Fin del documento**

