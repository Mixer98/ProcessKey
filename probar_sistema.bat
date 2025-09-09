@echo off
chcp 65001 >nul
echo =====================================================
echo          PRUEBA RÁPIDA DEL SISTEMA
echo =====================================================
echo.
echo Esta prueba verifica que todo esté funcionando...
echo.

cd /d "%~dp0"

echo 🧪 Probando importación de módulos...
python -c "
import sys
print(f'✅ Python {sys.version.split()[0]}')

try:
    import psutil
    print('✅ psutil - OK')
except ImportError:
    print('❌ psutil - FALTA')

try:
    import keyboard  
    print('✅ keyboard - OK')
except ImportError:
    print('❌ keyboard - FALTA')

try:
    import pynput
    print('✅ pynput - OK') 
except ImportError:
    print('❌ pynput - FALTA')

try:
    import pygame
    print('✅ pygame - OK')
except ImportError:
    print('❌ pygame - FALTA')

try:
    import tkinter
    print('✅ tkinter - OK')
except ImportError:
    print('❌ tkinter - FALTA')
"

if %errorLevel% neq 0 (
    echo.
    echo ❌ Error en la importación de módulos
    echo    Ejecuta: pip install -r requirements.txt
    goto end
)

echo.
echo 🔍 Probando lectura de procesos...
python -c "
import psutil
procesos = list(psutil.process_iter(['pid', 'name']))
print(f'✅ Se pueden leer {len(procesos)} procesos')
print(f'   Ejemplos: {[p.info[\"name\"] for p in procesos[:3]]}...')
"

if %errorLevel% neq 0 (
    echo ❌ Error al leer procesos
    goto end
)

echo.
echo 🎮 Probando interfaz gráfica...
python -c "
import tkinter as tk
root = tk.Tk()
root.withdraw()  # No mostrar la ventana
print('✅ Tkinter funciona correctamente')
root.destroy()
"

if %errorLevel% neq 0 (
    echo ❌ Error en la interfaz gráfica
    goto end
)

echo.
echo ✅ TODAS LAS PRUEBAS EXITOSAS
echo.
echo 🚀 El sistema está listo para usar.
echo    Puedes ejecutar la aplicación sin problemas.

:end
echo.
echo =====================================================
pause
