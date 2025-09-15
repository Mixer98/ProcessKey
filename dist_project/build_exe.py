#!/usr/bin/env python3
"""
Script para generar ejecutable del Administrador de Afinidad de Procesos
Ejecutar este script para crear el archivo .exe
"""

import os
import sys
import subprocess
import shutil

def main():
    print("🚀 Iniciando proceso de compilación...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("src/main.py"):
        print("❌ Error: No se encuentra src/main.py")
        print("   Asegúrate de ejecutar este script desde la carpeta dist_project")
        return False
    
    # Cambiar al directorio src
    os.chdir("src")
    
    # Comando PyInstaller optimizado
    cmd = [
        "pyinstaller",
        "--onefile",                          # Crear un solo archivo
        "--windowed",                         # Sin consola (GUI)
        "--name=AdministradorAfinidad",       # Nombre del ejecutable
        "--distpath=../exe",                  # Carpeta de salida
        "--workpath=../build",                # Carpeta de trabajo temporal
        "--specpath=../",                     # Donde guardar el .spec
        "--add-data=task_manager.py;.",       # Incluir módulos
        "--add-data=ui_components.py;.",      # Incluir módulos
        "--hidden-import=pygame",             # Importaciones ocultas
        "--hidden-import=pynput",
        "--hidden-import=psutil", 
        "--hidden-import=keyboard",
        "--hidden-import=tkinter",
        "--hidden-import=threading",
        "--hidden-import=json",
        "--hidden-import=ctypes",
        "--hidden-import=winsound",
        "--clean",                            # Limpiar cache
        "main.py"
    ]
    
    print(f"📦 Ejecutando: {' '.join(cmd)}")
    
    try:
        # Ejecutar PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Compilación exitosa!")
        
        # Volver al directorio anterior
        os.chdir("..")
        
        # Verificar que se creó el ejecutable
        exe_path = "exe/AdministradorAfinidad.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"🎯 Ejecutable creado: {exe_path}")
            print(f"📊 Tamaño: {size_mb:.1f} MB")
            
            # Copiar archivos de configuración junto al ejecutable
            config_files = ["config/automated_tasks.json"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    dest = f"exe/{os.path.basename(config_file)}"
                    shutil.copy2(config_file, dest)
                    print(f"📁 Copiado: {config_file} -> {dest}")
            
            print("\n🎉 ¡Proceso completado exitosamente!")
            print(f"📂 Encuentra tu ejecutable en: exe/AdministradorAfinidad.exe")
            return True
        else:
            print("❌ Error: No se pudo crear el ejecutable")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en la compilación:")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = main()
    input(f"\n{'✅ Presiona Enter para continuar...' if success else '❌ Presiona Enter para salir...'}")
