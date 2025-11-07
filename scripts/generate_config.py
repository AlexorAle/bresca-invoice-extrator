#!/usr/bin/env python3
"""
Script interactivo para generar config.yaml del dashboard con contraseña hasheada
"""
import sys
import os
from pathlib import Path
import bcrypt
import yaml
import secrets

def generate_cookie_key():
    """Generar clave aleatoria para cookie signature"""
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    """
    Hashear contraseña con bcrypt
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        Hash bcrypt
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def get_user_input():
    """Obtener datos del usuario de forma interactiva"""
    print("\n" + "="*60)
    print("📝 GENERADOR DE CONFIGURACIÓN DE DASHBOARD")
    print("="*60 + "\n")
    
    print("Ingresa los datos para el usuario administrador:\n")
    
    # Username
    username = input("Usuario (default: admin): ").strip() or "admin"
    
    # Nombre completo
    name = input("Nombre completo (default: Administrador): ").strip() or "Administrador"
    
    # Email
    email = input("Email: ").strip()
    while not email or '@' not in email:
        print("⚠️  Por favor ingresa un email válido")
        email = input("Email: ").strip()
    
    # Contraseña
    while True:
        password = input("Contraseña (mínimo 8 caracteres): ").strip()
        
        if len(password) < 8:
            print("⚠️  La contraseña debe tener al menos 8 caracteres")
            continue
        
        password_confirm = input("Confirmar contraseña: ").strip()
        
        if password != password_confirm:
            print("⚠️  Las contraseñas no coinciden")
            continue
        
        break
    
    return {
        'username': username,
        'name': name,
        'email': email,
        'password': password
    }

def create_config(user_data: dict) -> dict:
    """
    Crear diccionario de configuración
    
    Args:
        user_data: Datos del usuario
    
    Returns:
        Diccionario de configuración
    """
    # Hashear contraseña
    password_hash = hash_password(user_data['password'])
    
    # Generar clave de cookie
    cookie_key = generate_cookie_key()
    
    config = {
        'credentials': {
            'usernames': {
                user_data['username']: {
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'password': password_hash
                }
            }
        },
        'cookie': {
            'name': 'invoice_dashboard_auth',
            'key': cookie_key,
            'expiry_days': 30
        },
        'preauthorized': {
            'emails': []
        }
    }
    
    return config

def save_config(config: dict, output_path: Path):
    """
    Guardar configuración en archivo YAML
    
    Args:
        config: Diccionario de configuración
        output_path: Ruta del archivo de salida
    """
    # Asegurar que el directorio existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Guardar YAML
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n✅ Configuración guardada en: {output_path}")

def verify_config(config_path: Path):
    """
    Verificar que la configuración se puede cargar correctamente
    
    Args:
        config_path: Ruta del archivo de configuración
    
    Returns:
        True si es válida, False en caso contrario
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Verificar estructura básica
        required_keys = ['credentials', 'cookie']
        
        for key in required_keys:
            if key not in config:
                print(f"❌ Falta clave requerida: {key}")
                return False
        
        print("✅ Configuración válida")
        return True
    
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False

def main():
    """Función principal"""
    # Determinar ruta de salida
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'src' / 'dashboard' / 'config.yaml'
    
    # Verificar si ya existe
    if config_path.exists():
        print(f"\n⚠️  El archivo {config_path} ya existe")
        overwrite = input("¿Deseas sobrescribirlo? (s/N): ").strip().lower()
        
        if overwrite != 's':
            print("❌ Operación cancelada")
            return 1
        
        # Hacer backup del archivo existente
        backup_path = config_path.with_suffix('.yaml.bak')
        import shutil
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backup creado en: {backup_path}")
    
    # Obtener datos del usuario
    try:
        user_data = get_user_input()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por usuario")
        return 130
    
    # Crear configuración
    print("\n🔐 Generando hash de contraseña...")
    config = create_config(user_data)
    
    # Guardar
    save_config(config, config_path)
    
    # Verificar
    print("\n🔍 Verificando configuración...")
    if not verify_config(config_path):
        print("⚠️  La configuración puede tener problemas")
        return 1
    
    # Instrucciones finales
    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*60)
    print(f"\nUsuario: {user_data['username']}")
    print(f"Email: {user_data['email']}")
    print(f"\nPara iniciar el dashboard, ejecuta:")
    print(f"  cd {project_root}")
    print(f"  streamlit run src/dashboard/app.py")
    print("\nAccede con:")
    print(f"  Usuario: {user_data['username']}")
    print(f"  Contraseña: (la que ingresaste)")
    print("\n⚠️  IMPORTANTE: Guarda las credenciales en un lugar seguro")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
