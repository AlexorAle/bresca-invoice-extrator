# Fase 1: Setup de Infraestructura

## Requisitos Previos
- VPS con Ubuntu 22.04 o Debian 11+
- Acceso SSH con sudo
- Mínimo 8GB RAM, 20GB disco
- Conexión a internet

## Instalación

### 1. Conectar al VPS
```bash
ssh alex@tu-vps-ip
cd /home/alex/proyectos/invoice-extractor
```

### 2. Ejecutar Setup
```bash
chmod +x infra/setup.sh
./infra/setup.sh
```

**Duración:** ~10-15 minutos (depende de descarga de Ollama y modelo)

### 3. Verificar Instalación
```bash
./infra/smoke_test.sh
```

Debe mostrar ✓ en todos los checks.

## Componentes Instalados

- **PostgreSQL 14+**: Base de datos relacional
- **Ollama + Llama 3.2 Vision 3B**: OCR primario (local, gratuito)
- **Tesseract OCR**: OCR fallback
- **Python 3.9+**: Runtime de la aplicación
- **Poppler**: Conversión PDF a imagen

## Estructura Creada

```
invoice-extractor/
├── infra/          # Scripts de infraestructura
├── src/            # Código fuente (vacío, fase 2)
│   ├── db/
│   ├── pipeline/
│   ├── dashboard/
│   └── security/
├── data/           # Datos persistentes
│   ├── quarantine/
│   ├── pending/
│   └── backups/
├── temp/           # Archivos temporales
├── logs/           # Logs de aplicación
├── scripts/        # Utilidades
└── venv/           # Virtual environment Python
```

## Base de Datos

**Nombre:** `negocio_db`  
**Usuario:** `extractor_user`  
**Password:** `changeme_produccion` ⚠ **CAMBIAR EN PRODUCCIÓN**  
**Puerto:** 5432 (solo localhost)  
**Tablas principales:**
- `facturas`: Facturas procesadas
- `proveedores`: Catálogo de proveedores
- `ingest_events`: Eventos de auditoría

### Cambiar contraseña de PostgreSQL

```bash
sudo -u postgres psql
```

```sql
ALTER USER extractor_user WITH PASSWORD 'tu_password_segura_aqui';
\q
```

Luego actualiza el archivo `.env` con la nueva contraseña.

## Servicios Systemd

### Ollama

```bash
# Estado
sudo systemctl status ollama

# Reiniciar
sudo systemctl restart ollama

# Logs
sudo journalctl -u ollama -f
```

**Puerto:** 11434 (localhost)  
**Modelo:** llama3.2-vision:3b

### PostgreSQL

```bash
# Estado
sudo systemctl status postgresql

# Reiniciar
sudo systemctl restart postgresql

# Logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## Troubleshooting

### Ollama no responde

```bash
# Verificar si está corriendo
curl http://localhost:11434/api/tags

# Si falla:
sudo systemctl restart ollama
sleep 5
curl http://localhost:11434/api/tags

# Si el modelo no está descargado:
ollama pull llama3.2-vision:3b
```

### PostgreSQL no conecta

```bash
# Verificar servicio
sudo systemctl status postgresql

# Conectar como superusuario
sudo -u postgres psql

# Listar bases de datos
\l

# Conectar a negocio_db
\c negocio_db

# Listar tablas
\dt

# Salir
\q
```

### Python packages faltan

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Permisos denegados

```bash
# Verificar permisos de scripts
chmod +x infra/*.sh

# Verificar usuario del servicio Ollama
sudo systemctl edit ollama.service
# Debe tener: User=alex (o tu usuario)
```

## Próximos Pasos

1. **Cambiar contraseña de PostgreSQL** (ver arriba)
2. **Configurar .env** basado en `.env.example`:
   ```bash
   cp .env.example .env
   nano .env
   ```
3. **Subir service_account.json** de Google Drive:
   ```bash
   # Desde tu máquina local
   scp service_account.json alex@tu-vps:/home/alex/proyectos/invoice-extractor/
   chmod 600 service_account.json
   ```
4. **Subir código Python** (Fase 2)
5. **Ejecutar tests de código**

## Logs

- **Setup:** `infra/setup.log`
- **Ollama:** `sudo journalctl -u ollama`
- **PostgreSQL:** `/var/log/postgresql/postgresql-*.log`
- **Aplicación:** `logs/extractor.log` (cuando se implemente)

## Verificación Rápida

Después del setup, verifica que todo funciona:

```bash
# 1. PostgreSQL
PGPASSWORD='changeme_produccion' psql -U extractor_user -h localhost -d negocio_db -c "SELECT COUNT(*) FROM facturas;"

# 2. Ollama
curl http://localhost:11434/api/tags | grep llama3.2-vision

# 3. Tesseract
tesseract --version && tesseract --list-langs | grep spa

# 4. Python
source venv/bin/activate && python3 --version
```

Todos deben responder sin errores.

## Notas Importantes

- ⚠ **Seguridad**: Cambia la contraseña de PostgreSQL antes de usar en producción
- ⚠ **Ollama**: El modelo llama3.2-vision:3b ocupa ~2GB de espacio en disco
- ⚠ **Backups**: Configura backups regulares de la base de datos (ver scripts/)
- 📝 **Logs**: Revisa `infra/setup.log` si hay problemas durante la instalación

