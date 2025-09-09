#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del Administrador de Afinidad
"""

import sys
import os

def test_imports():
    """Prueba las importaciones necesarias"""
    print("=== Prueba de Importaciones ===")
    
    try:
        import tkinter
        print("✓ tkinter disponible")
    except ImportError as e:
        print(f"❌ tkinter no disponible: {e}")
        return False
    
    try:
        import psutil
        print(f"✓ psutil disponible (versión {psutil.__version__})")
    except ImportError as e:
        print(f"❌ psutil no disponible: {e}")
        return False
    
    return True

def test_system_info():
    """Muestra información del sistema"""
    print("\n=== Información del Sistema ===")
    
    try:
        import psutil
        
        # Información de CPU
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        print(f"CPUs físicas: {cpu_count}")
        print(f"CPUs lógicas: {cpu_count_logical}")
        
        # Información de procesos
        process_count = len(list(psutil.process_iter()))
        print(f"Procesos en ejecución: {process_count}")
        
        # Verificar permisos
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            print(f"Permisos de administrador: {'✓ Sí' if is_admin else '❌ No'}")
        except:
            print("Permisos de administrador: ❓ No se pudo determinar")
            
    except Exception as e:
        print(f"Error obteniendo información del sistema: {e}")

def test_affinity_manager():
    """Prueba la importación del módulo principal"""
    print("\n=== Prueba del Módulo Principal ===")
    
    try:
        import affinity_manager
        print("✓ affinity_manager importado correctamente")
        
        # Verificar clase principal
        if hasattr(affinity_manager, 'AffinityManager'):
            print("✓ Clase AffinityManager disponible")
        else:
            print("❌ Clase AffinityManager no encontrada")
            
        return True
    except ImportError as e:
        print(f"❌ Error importando affinity_manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("Administrador de Afinidad de Procesos - Prueba del Sistema")
    print("=" * 60)
    
    success = True
    
    # Prueba de importaciones
    if not test_imports():
        success = False
    
    # Información del sistema
    test_system_info()
    
    # Prueba del módulo principal
    if not test_affinity_manager():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Todas las pruebas pasaron exitosamente!")
        print("La aplicación debería funcionar correctamente.")
        print("\nPara ejecutar la aplicación:")
        print("  python affinity_manager.py")
        print("\nO usar los scripts de lanzamiento:")
        print("  run_as_admin.bat")
        print("  run_as_admin.ps1")
    else:
        print("❌ Algunas pruebas fallaron.")
        print("Revisar las dependencias e instalación.")
    
    print("\nPresione Enter para continuar...")
    input()

if __name__ == "__main__":
    main()
