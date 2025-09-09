@echo off
chcp 65001 >nul
echo =====================================================
echo    Administrador de Afinidad de CPU - Ejecutor
echo =====================================================
echo.
echo Este script evita los problemas de PowerShell
echo ejecutando directamente con CMD.
echo.

:: Cambiar al directorio del script
cd /d "%~dp0"

echo Verificando entorno Python...
echo.

:: Opción 1: Intentar con entorno virtual usando activate.bat
if exist ".venv\Scripts\activate.bat" (
    echo ✓ Entorno virtual encontrado
    echo   Activando entorno virtual...
    call .venv\Scripts\activate.bat
    echo   Ejecutando aplicación...
    echo.
    python affinity_manager.py
    goto :end
)

:: Opción 2: Ejecutar con Python global
echo ! Entorno virtual no encontrado
echo   Intentando con Python global...
echo.

python --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Python encontrado
    echo   Verificando dependencias...
    python -c "import psutil, keyboard, pynput, pygame" >nul 2>&1
    if %errorLevel% == 0 (
        echo ✓ Dependencias encontradas
        echo   Ejecutando aplicación...
        echo.
        python affinity_manager.py
    ) else (
        echo ✗ Faltan dependencias. Instalando...
        echo.
        pip install -r requirements.txt
        echo.
        echo   Ejecutando aplicación...
        python affinity_manager.py
    )
) else (
    echo ✗ Python no encontrado en el PATH
    echo.
    echo Por favor:
    echo 1. Instala Python desde python.org
    echo 2. O ejecuta desde el directorio de Python
    echo.
    pause
)

:end
echo.
echo =====================================================
echo Aplicación finalizada. Presiona cualquier tecla...
pause >nul
