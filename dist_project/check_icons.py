#!/usr/bin/env python3
"""
Script para verificar y preparar el sistema de iconos
"""

import os
import sys

def check_pillow():
    """Verifica si Pillow está instalado"""
    try:
        from PIL import Image, ImageTk
        print("✅ Pillow está instalado correctamente")
        return True
    except ImportError:
        print("❌ Pillow no está instalado")
        print("   Para instalarlo ejecuta: pip install Pillow")
        return False

def check_icons_directory():
    """Verifica si el directorio de iconos existe"""
    # Buscar iconos en las rutas posibles
    possible_dirs = [
        "src/assets/icons",
        "assets/icons"
    ]
    
    icons_dir = None
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            icons_dir = dir_path
            break
    
    if icons_dir:
        print(f"✅ Directorio de iconos encontrado: {icons_dir}")
        
        # Listar iconos disponibles
        icon_files = [f for f in os.listdir(icons_dir) if f.endswith('.png')]
        print(f"   Iconos disponibles: {len(icon_files)}")
        
        if len(icon_files) > 0:
            print("   Algunos iconos encontrados:")
            for icon in sorted(icon_files)[:5]:
                print(f"     - {icon}")
            if len(icon_files) > 5:
                print(f"     ... y {len(icon_files) - 5} más")
        
        return True
    else:
        print(f"❌ Directorio de iconos no encontrado: {icons_dir}")
        print("   Necesitas crear el directorio y agregar los archivos PNG")
        return False

def check_source_files():
    """Verifica si los archivos fuente están presentes"""
    src_files = [
        "src/main.py",
        "src/ui_components.py", 
        "src/task_manager.py",
        "src/icon_utils.py"
    ]
    
    all_present = True
    for file in src_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} no encontrado")
            all_present = False
    
    return all_present

def create_icons_directory():
    """Crea el directorio de iconos si no existe"""
    # Crear en src/assets/icons por defecto
    icons_dir = "src/assets/icons"
    os.makedirs(icons_dir, exist_ok=True)
    print(f"📁 Directorio creado: {icons_dir}")
    
    # Crear un archivo README en el directorio
    readme_content = """# Directorio de Iconos

Coloca aquí los archivos PNG para los iconos de la aplicación.

Iconos requeridos:
- BarChart.png, CheckMark.png, Clipboard.png, ControlKnobs.png
- Counterclockwise.png, CrossMark.png, DesktopComputer.png
- Eye.png, Gear.png, green.png, GrennHeart.png, Heart.png
- Information.png, Keyboard.png, Memo.png, Pencil.png
- red.png, Rocket.png, Skull.png, Target.png, TestTube.png
- WarningSign.png, Wastebasket.png, White.png, Wrench.png, yelow.png

Tamaño recomendado: 16x16 o 24x24 píxeles
Formato: PNG con transparencia
"""
    
    readme_path = os.path.join(icons_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📝 Creado: {readme_path}")

def main():
    """Función principal"""
    print("🔍 Verificando sistema de iconos...\n")
    
    # Verificar dependencias
    print("1. Verificando dependencias:")
    pillow_ok = check_pillow()
    print()
    
    # Verificar archivos fuente
    print("2. Verificando archivos fuente:")
    sources_ok = check_source_files()
    print()
    
    # Verificar directorio de iconos
    print("3. Verificando directorio de iconos:")
    icons_ok = check_icons_directory()
    print()
    
    # Crear directorio si no existe
    if not icons_ok:
        print("4. Creando directorio de iconos:")
        create_icons_directory()
        print()
    
    # Resumen
    print("📋 Resumen:")
    if pillow_ok and sources_ok:
        if icons_ok:
            print("✅ Sistema de iconos listo para usar")
            print("   La aplicación usará iconos PNG cuando estén disponibles")
        else:
            print("⚠️  Sistema de iconos parcialmente listo")
            print("   Agrega los archivos PNG al directorio assets/icons/")
            print("   La aplicación usará emojis como fallback")
    else:
        print("❌ Sistema de iconos no está listo")
        if not pillow_ok:
            print("   - Instala Pillow: pip install Pillow")
        if not sources_ok:
            print("   - Faltan archivos fuente modificados")
    
    print("\nPara probar el sistema ejecuta: python test_icons.py")

if __name__ == "__main__":
    main()
