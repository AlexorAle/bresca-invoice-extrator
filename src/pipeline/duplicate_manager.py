"""
Gestor de detección y manejo de duplicados

Implementa la lógica de decisión para:
- Detectar duplicados exactos (mismo hash)
- Detectar duplicados lógicos (mismo proveedor+número, distinto importe)
- Mover archivos a cuarentena
- Registrar eventos de auditoría
"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
from enum import Enum

from src.logging_conf import get_logger

logger = get_logger(__name__)

class DuplicateDecision(Enum):
    """Decisiones posibles para duplicados"""
    INSERT = 'insert'
    IGNORE = 'ignore'
    DUPLICATE = 'duplicate'
    REVIEW = 'review'
    UPDATE_REVISION = 'update_revision'

class DuplicateManager:
    """Gestor de duplicados"""
    
    def __init__(self, quarantine_base_path: str = None):
        """Inicializar gestor"""
        self.quarantine_base_path = Path(
            quarantine_base_path or os.getenv('QUARANTINE_PATH', 'data/quarantine')
        )
        
        self.duplicates_path = self.quarantine_base_path / 'duplicates'
        self.review_path = self.quarantine_base_path / 'review'
        
        self.duplicates_path.mkdir(parents=True, exist_ok=True)
        self.review_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DuplicateManager inicializado")
    
    def decide_action(
        self,
        factura_dto: dict,
        existing_by_file_id: Optional[dict],
        existing_by_hash: Optional[dict],
        existing_by_number: Optional[dict]
    ) -> Tuple[DuplicateDecision, str]:
        """Decidir acción basándose en facturas existentes"""
        drive_file_id = factura_dto.get('drive_file_id')
        hash_contenido = factura_dto.get('hash_contenido')
        proveedor = factura_dto.get('proveedor_text', '')
        numero = factura_dto.get('numero_factura', '')
        importe = factura_dto.get('importe_total')
        
        if existing_by_file_id:
            existing_hash = existing_by_file_id.get('hash_contenido')
            
            if hash_contenido and existing_hash and hash_contenido != existing_hash:
                return (
                    DuplicateDecision.UPDATE_REVISION,
                    f"Archivo modificado: hash cambió"
                )
            
            return (
                DuplicateDecision.IGNORE,
                f"Archivo ya procesado: drive_file_id={drive_file_id}"
            )
        
        if existing_by_hash and hash_contenido:
            existing_file_id = existing_by_hash.get('drive_file_id')
            existing_file_name = existing_by_hash.get('drive_file_name', 'unknown')
            
            return (
                DuplicateDecision.DUPLICATE,
                f"Duplicado detectado: mismo contenido que '{existing_file_name}'"
            )
        
        if existing_by_number:
            existing_importe = existing_by_number.get('importe_total')
            
            if existing_importe and importe and abs(float(existing_importe) - float(importe)) > 0.02:
                return (
                    DuplicateDecision.REVIEW,
                    f"Posible conflicto: mismo proveedor y número, distinto importe"
                )
        
        return (
            DuplicateDecision.INSERT,
            "Nueva factura, proceder con inserción"
        )
    
    def move_to_quarantine(
        self,
        file_info: dict,
        decision: DuplicateDecision,
        factura_dto: dict,
        reason: str
    ) -> Optional[str]:
        """Mover archivo a cuarentena con metadata"""
        try:
            local_path = file_info.get('local_path')
            file_name = file_info.get('name', 'unknown.pdf')
            drive_file_id = file_info.get('id')
            
            if not local_path or not os.path.exists(local_path):
                logger.warning(f"No se puede mover a cuarentena, archivo no existe: {local_path}")
                return None
            
            if decision == DuplicateDecision.DUPLICATE:
                dest_folder = self.duplicates_path
            elif decision == DuplicateDecision.REVIEW:
                dest_folder = self.review_path
            else:
                dest_folder = self.quarantine_base_path / 'otros'
                dest_folder.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
            safe_name = self._sanitize_filename(file_name)
            quarantine_file = dest_folder / f"{timestamp}_{decision.value}_{safe_name}"
            
            shutil.copy2(local_path, quarantine_file)
            
            meta_file = quarantine_file.with_suffix('.meta.json')
            metadata = {
                'timestamp': timestamp,
                'decision': decision.value,
                'reason': reason,
                'drive_file_id': drive_file_id,
                'drive_file_name': file_name,
                'factura_data': {
                    'proveedor_text': factura_dto.get('proveedor_text'),
                    'numero_factura': factura_dto.get('numero_factura'),
                    'fecha_emision': factura_dto.get('fecha_emision'),
                    'importe_total': str(factura_dto.get('importe_total')) if factura_dto.get('importe_total') else None,
                    'hash_contenido': factura_dto.get('hash_contenido')
                },
                'quarantined_at': datetime.utcnow().isoformat()
            }
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Archivo movido a cuarentena: {quarantine_file}")
            
            return str(quarantine_file)
        
        except Exception as e:
            logger.error(f"Error moviendo archivo a cuarentena: {e}", exc_info=True)
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizar nombre de archivo"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
        return filename
    
    def create_audit_log(
        self,
        drive_file_id: str,
        decision: DuplicateDecision,
        reason: str,
        factura_dto: dict
    ) -> dict:
        """Crear log de auditoría en formato JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'drive_file_id': drive_file_id,
            'hash_contenido': factura_dto.get('hash_contenido'),
            'decision': decision.value,
            'estado': self._decision_to_estado(decision),
            'detalle': reason,
            'factura_data': {
                'proveedor_text': factura_dto.get('proveedor_text'),
                'numero_factura': factura_dto.get('numero_factura'),
                'fecha_emision': factura_dto.get('fecha_emision'),
                'importe_total': str(factura_dto.get('importe_total')) if factura_dto.get('importe_total') else None
            }
        }
        
        return log_entry
    
    def _decision_to_estado(self, decision: DuplicateDecision) -> str:
        """Mapear decisión a estado de BD"""
        mapping = {
            DuplicateDecision.INSERT: 'procesado',
            DuplicateDecision.IGNORE: 'procesado',
            DuplicateDecision.DUPLICATE: 'duplicado',
            DuplicateDecision.REVIEW: 'revisar',
            DuplicateDecision.UPDATE_REVISION: 'procesado'
        }
        return mapping.get(decision, 'procesado')
    
    def cleanup_old_quarantine(self, days: int = 90):
        """Limpiar archivos antiguos de cuarentena"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        removed_count = 0
        
        for folder in [self.duplicates_path, self.review_path]:
            if not folder.exists():
                continue
            
            for file_path in folder.glob('*'):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Error eliminando archivo antiguo: {e}")
        
        if removed_count > 0:
            logger.info(f"Limpiados {removed_count} archivos de cuarentena antiguos")
