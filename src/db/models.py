"""
Modelos SQLAlchemy para las tablas de la base de datos
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, ForeignKey, CheckConstraint, DECIMAL, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Proveedor(Base):
    """Tabla de proveedores/clientes"""
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False, unique=True)
    nif_cif = Column(Text)
    email_contacto = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    # Relación con facturas
    facturas = relationship("Factura", back_populates="proveedor")

class Factura(Base):
    """Tabla principal de facturas"""
    __tablename__ = 'facturas'
    
    id = Column(BigInteger, primary_key=True)
    drive_file_id = Column(Text, nullable=False, unique=True)
    drive_file_name = Column(Text, nullable=False)
    drive_folder_name = Column(Text, nullable=False)
    
    proveedor_id = Column(BigInteger, ForeignKey('proveedores.id'))
    proveedor_text = Column(Text)
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
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con proveedor
    proveedor = relationship("Proveedor", back_populates="facturas")
    
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
