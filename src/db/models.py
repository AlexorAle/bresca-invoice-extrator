"""
Modelos SQLAlchemy para las tablas de la base de datos
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, ForeignKey, CheckConstraint, DECIMAL, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Proveedor(Base):
    """Tabla de proveedores/clientes (LEGACY - mantener para compatibilidad)"""
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False, unique=True)
    categoria = Column(Text)  # Nueva columna para categorización
    nif_cif = Column(Text)
    email_contacto = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    # Relación con facturas
    facturas = relationship("Factura", back_populates="proveedor")


class ProveedorMaestro(Base):
    """Tabla maestra de proveedores normalizados y unificados"""
    __tablename__ = 'proveedores_maestros'
    
    id = Column(Integer, primary_key=True)
    nombre_canonico = Column(Text, nullable=False, unique=True)
    nif_cif = Column(Text, unique=True, nullable=True)
    nombres_alternativos = Column(JSONB, nullable=False, default=list)
    total_facturas = Column(Integer, default=0)
    total_importe = Column(DECIMAL(18, 2), default=0.00)
    categoria = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con facturas (opcional, para tracking)
    facturas = relationship("Factura", foreign_keys="Factura.proveedor_maestro_id", back_populates="proveedor_maestro")
    
    __table_args__ = (
        Index('idx_proveedores_maestros_nif', 'nif_cif', postgresql_where=(nif_cif != None)),
        Index('idx_proveedores_maestros_nombre', 'nombre_canonico'),
    )

class Factura(Base):
    """Tabla principal de facturas"""
    __tablename__ = 'facturas'
    
    id = Column(BigInteger, primary_key=True)
    drive_file_id = Column(Text, nullable=False, unique=True)
    drive_file_name = Column(Text, nullable=False)
    drive_folder_name = Column(Text, nullable=False)
    
    proveedor_id = Column(BigInteger, ForeignKey('proveedores.id'))
    proveedor_text = Column(Text)
    proveedor_maestro_id = Column(Integer, ForeignKey('proveedores_maestros.id'), nullable=True)
    numero_factura = Column(Text)
    moneda = Column(Text, default='EUR')
    fecha_emision = Column(Date)
    fecha_recepcion = Column(DateTime)
    
    base_imponible = Column(DECIMAL(18, 2))
    impuestos_total = Column(DECIMAL(18, 2))
    iva_porcentaje = Column(DECIMAL(5, 2))
    importe_total = Column(DECIMAL(18, 2), nullable=True)  # Permitir NULL para facturas en estado 'revisar' o 'error'
    
    conceptos_json = Column(JSONB)
    metadatos_json = Column(JSONB)
    
    pagina_analizada = Column(Integer, default=1)
    extractor = Column(Text, nullable=False)
    confianza = Column(Text)
    hash_contenido = Column(Text)
    revision = Column(Integer, default=1)
    drive_modified_time = Column(DateTime)
    
    estado = Column(Text, default='procesado')
    error_msg = Column(Text)
    
    # Campos para reprocesamiento automático
    reprocess_attempts = Column(Integer, default=0)
    reprocessed_at = Column(DateTime)
    reprocess_reason = Column(Text)
    
    # Campo para archivos eliminados de Drive
    deleted_from_drive = Column(Boolean, default=False)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con proveedor (legacy)
    proveedor = relationship("Proveedor", back_populates="facturas")
    # Relación con proveedor maestro
    proveedor_maestro = relationship("ProveedorMaestro", back_populates="facturas")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('char_length(moneda) = 3', name='check_moneda_length'),
        CheckConstraint('base_imponible >= 0', name='check_base_imponible_positive'),
        CheckConstraint('impuestos_total >= 0', name='check_impuestos_positive'),
        # Removido constraint que impedía valores negativos - ahora se permiten facturas con importe negativo
        CheckConstraint("confianza IN ('alta', 'media', 'baja')", name='check_confianza_values'),
        CheckConstraint("estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente')", name='check_estado_values'),
        CheckConstraint('reprocess_attempts >= 0', name='check_reprocess_attempts_positive'),
        Index('idx_facturas_hash_contenido_unique', 'hash_contenido', unique=True, postgresql_where=(hash_contenido != None)),
        Index('idx_facturas_proveedor_numero', 'proveedor_text', 'numero_factura'),
        Index('idx_facturas_estado', 'estado'),
        Index('idx_facturas_drive_modified', 'drive_modified_time'),
        Index('idx_facturas_deleted', 'deleted_from_drive', postgresql_where=(deleted_from_drive == True)),
    )

class IngestEvent(Base):
    """Tabla de eventos de auditoría"""
    __tablename__ = 'ingest_events'
    
    id = Column(BigInteger, primary_key=True)
    drive_file_id = Column(Text, nullable=False)
    etapa = Column(Text, nullable=False)
    nivel = Column(Text, nullable=False)
    detalle = Column(Text)
    hash_contenido = Column(Text)
    decision = Column(Text)
    ts = Column(DateTime, default=datetime.utcnow)

class SyncState(Base):
    """Tabla de estado de sincronización incremental"""
    __tablename__ = 'sync_state'
    
    key = Column(Text, primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Categoria(Base):
    """Tabla de categorías para proveedores y otros usos"""
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    color = Column(Text, default='#3b82f6')  # Color hexadecimal para identificación visual
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_categorias_nombre', 'nombre'),
        Index('idx_categorias_activo', 'activo', postgresql_where=(activo == True)),
    )
