#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de tareas del Affinity Manager
Ejecute este script para diagnosticar problemas con el sistema de tareas.
"""

import json
import os

def test_task_file():
    """Prueba el archivo de tareas automatizadas"""
    print("🔍 Probando archivo de tareas automatizadas...")
    
    tasks_file = "automated_tasks.json"
    
    if not os.path.exists(tasks_file):
        print(f"❌ Archivo {tasks_file} no encontrado")
        return
    
    print(f"✅ Archivo {tasks_file} encontrado")
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        print(f"✅ Archivo JSON válido")
        print(f"📊 Total de tareas: {len(tasks_data)}")
        
        for task_id, task_data in tasks_data.items():
            print(f"\n📋 Tarea ID: {task_id}")
            print(f"   Nombre: {task_data.get('name', 'NO DEFINIDO')}")
            print(f"   Proceso: {task_data.get('process_name', 'NO DEFINIDO')}")
            print(f"   Hotkey: {task_data.get('hotkey', 'NO DEFINIDO')}")
            
            # Verificar campos obligatorios
            required_fields = ['name', 'process_name', 'hotkey', 'high_affinity', 'low_affinity']
            missing_fields = []
            
            for field in required_fields:
                if field not in task_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   ❌ Campos faltantes: {', '.join(missing_fields)}")
            else:
                print(f"   ✅ Campos obligatorios presentes")
            
            # Verificar campos opcionales
            if 'alert_type' not in task_data:
                print(f"   ⚠️ Campo 'alert_type' faltante (se agregará automáticamente)")
            else:
                print(f"   ✅ Tipo de alerta: {task_data['alert_type']}")
            
            if 'custom_notification' not in task_data:
                print(f"   ℹ️ Sin notificaciones personalizadas")
            else:
                print(f"   ✅ Notificaciones personalizadas configuradas")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error de formato JSON: {str(e)}")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {str(e)}")

def fix_task_file():
    """Corrige automáticamente el archivo de tareas"""
    print("\n🔧 Corrigiendo archivo de tareas...")
    
    tasks_file = "automated_tasks.json"
    
    if not os.path.exists(tasks_file):
        print(f"❌ Archivo {tasks_file} no encontrado")
        return
    
    try:
        # Crear backup
        backup_file = tasks_file + ".backup"
        print(f"📦 Creando backup: {backup_file}")
        
        with open(tasks_file, 'r', encoding='utf-8') as f:
            original_data = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_data)
        
        # Cargar y corregir datos
        tasks_data = json.loads(original_data)
        corrected_count = 0
        
        for task_id, task_data in tasks_data.items():
            # Agregar campos faltantes
            if 'alert_type' not in task_data:
                task_data['alert_type'] = 'combinado'
                corrected_count += 1
                print(f"   ✅ Agregado 'alert_type' a tarea: {task_data.get('name', 'Sin nombre')}")
            
            if 'custom_notification' not in task_data:
                task_data['custom_notification'] = None
                corrected_count += 1
                print(f"   ✅ Agregado 'custom_notification' a tarea: {task_data.get('name', 'Sin nombre')}")
        
        if corrected_count > 0:
            # Guardar archivo corregido
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Archivo corregido. {corrected_count} campos agregados.")
        else:
            print("ℹ️ No se necesitaron correcciones.")
        
    except Exception as e:
        print(f"❌ Error corrigiendo archivo: {str(e)}")

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando diagnóstico del sistema de tareas")
    print("=" * 50)
    
    # Probar archivo de tareas
    test_task_file()
    
    # Preguntar si quiere corregir
    print("\n" + "=" * 50)
    response = input("¿Desea intentar corregir automáticamente el archivo? (s/n): ").lower().strip()
    
    if response in ['s', 'si', 'yes', 'y']:
        fix_task_file()
        print("\n🔄 Ejecutando prueba nuevamente después de las correcciones...")
        print("=" * 50)
        test_task_file()
    
    print("\n🏁 Diagnóstico completado.")
    print("💡 Ahora puede ejecutar el Affinity Manager normalmente.")

if __name__ == "__main__":
    main()
