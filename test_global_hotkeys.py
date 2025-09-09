#!/usr/bin/env python3
"""
Script de prueba para verificar hotkeys globales
Prueba que los hotkeys funcionen incluso cuando la aplicación no tiene el foco
"""

import keyboard
import time
import threading

def test_global_hotkeys():
    """Prueba los hotkeys globales"""
    print("=== Prueba de Hotkeys Globales ===")
    print("Este script prueba que los hotkeys funcionen globalmente")
    print("Abre cualquier aplicación (navegador, juego, etc.) y prueba los hotkeys")
    print()
    
    # Contador de pruebas
    test_count = 0
    
    def on_test_hotkey():
        nonlocal test_count
        test_count += 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ Hotkey detectado! (Prueba #{test_count})")
        print(f"    - Funciona incluso cuando esta ventana no tiene el foco")
        print(f"    - Abre cualquier aplicación y presiona Ctrl+Alt+T")
        print()
    
    def on_exit_hotkey():
        print("\n🛑 Hotkey de salida detectado (Ctrl+Alt+Q)")
        print("Finalizando prueba...")
        exit(0)
    
    # Configurar hotkeys de prueba
    try:
        keyboard.add_hotkey('ctrl+alt+t', on_test_hotkey, suppress=False)
        keyboard.add_hotkey('ctrl+alt+q', on_exit_hotkey, suppress=False)
        
        print("🎯 Hotkeys configurados:")
        print("  - Ctrl+Alt+T: Prueba el hotkey global")  
        print("  - Ctrl+Alt+Q: Salir de la prueba")
        print()
        print("💡 Instrucciones:")
        print("  1. Abre cualquier aplicación (Chrome, Notepad, juego)")
        print("  2. Presiona Ctrl+Alt+T desde esa aplicación")
        print("  3. El hotkey debería funcionar sin importar qué app tenga el foco")
        print("  4. Presiona Ctrl+Alt+Q para terminar la prueba")
        print()
        print("⏳ Esperando hotkeys... (prueba abriendo otras aplicaciones)")
        
        # Mantener el script activo
        start_time = time.time()
        while True:
            time.sleep(1)
            
            # Mostrar recordatorio cada 30 segundos
            if int(time.time() - start_time) % 30 == 0:
                elapsed = int(time.time() - start_time)
                print(f"⏱️  Tiempo transcurrido: {elapsed}s | Pruebas exitosas: {test_count}")
                
    except KeyboardInterrupt:
        print("\n\n⚡ Interrumpido por usuario (Ctrl+C)")
        print("Prueba finalizada.")
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        print("Posibles causas:")
        print("  - Faltan permisos de administrador")
        print("  - Otro programa está capturando los hotkeys")
        print("  - Problema con la librería keyboard")

def test_process_detection():
    """Prueba la detección de procesos"""
    print("\n=== Prueba de Detección de Procesos ===")
    
    try:
        import psutil
        
        # Buscar algunos procesos comunes
        common_processes = ['explorer.exe', 'winlogon.exe', 'svchost.exe', 'dwm.exe']
        found_processes = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in common_processes:
                    found_processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("✅ Procesos del sistema detectados:")
        for process in found_processes[:5]:  # Mostrar primeros 5
            print(f"  - {process}")
        
        print(f"\n📊 Total de procesos en ejecución: {len(list(psutil.process_iter()))}")
        
        # Verificar acceso a afinidad
        try:
            current_process = psutil.Process()
            affinity = current_process.cpu_affinity()
            print(f"✅ Afinidad del proceso actual: {affinity}")
        except Exception as e:
            print(f"⚠️  No se pudo acceder a afinidad: {e}")
        
    except ImportError:
        print("❌ psutil no está instalado")
    except Exception as e:
        print(f"❌ Error en detección de procesos: {e}")

def main():
    """Función principal de prueba"""
    print("Administrador de Afinidad - Prueba del Sistema")
    print("=" * 50)
    
    # Verificar dependencias
    try:
        import keyboard
        import psutil
        print("✅ Todas las dependencias están instaladas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("Ejecutar: pip install keyboard psutil")
        return
    
    # Verificar permisos
    import os
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        # Windows
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            is_admin = False
    
    if is_admin:
        print("✅ Ejecutándose como administrador")
    else:
        print("⚠️  No se detectaron permisos de administrador")
        print("   Algunas funciones pueden estar limitadas")
    
    print()
    
    # Ejecutar pruebas
    test_process_detection()
    
    print("\n" + "=" * 50)
    print("🚀 Iniciando prueba de hotkeys globales...")
    print("   Mantén esta ventana abierta pero cambia a otras aplicaciones")
    print()
    
    test_global_hotkeys()

if __name__ == "__main__":
    main()
