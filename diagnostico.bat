@echo off
chcp 65001 >nul
echo =====================================================
echo           DIAGNÓSTICO DEL SISTEMA
echo =====================================================
echo.
echo Verificando el estado del sistema...
echo.

:: Cambiar al directorio del script
cd /d "%~dp0"

echo 📁 Directorio actual:
echo %cd%
echo.

echo 🐍 Verificando Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
) else (
    echo ❌ Python no encontrado en PATH
    echo    Instala Python desde: https://python.org
)
echo.

echo 📦 Verificando pip...
pip --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=1,2" %%i in ('pip --version') do echo ✅ pip %%j
) else (
    echo ❌ pip no disponible
)
echo.

echo 🌐 Verificando entorno virtual...
if exist ".venv\" (
    echo ✅ Directorio .venv encontrado
    if exist ".venv\Scripts\activate.bat" (
        echo ✅ Script activate.bat encontrado
    ) else (
        echo ⚠️  activate.bat no encontrado
    )
    
    if exist ".venv\Scripts\Activate.ps1" (
        echo ✅ Script Activate.ps1 encontrado
    ) else (
        echo ⚠️  Activate.ps1 no encontrado
    )
) else (
    echo ❌ Entorno virtual no encontrado
    echo    Crea uno con: python -m venv .venv
)
echo.

echo 📋 Verificando archivos principales...
if exist "affinity_manager.py" (
    echo ✅ affinity_manager.py
) else (
    echo ❌ affinity_manager.py NO ENCONTRADO
)

if exist "requirements.txt" (
    echo ✅ requirements.txt
) else (
    echo ❌ requirements.txt NO ENCONTRADO
)
echo.

echo 📚 Verificando dependencias críticas...

:: Verificar psutil
python -c "import psutil; print(f'✅ psutil {psutil.__version__}')" 2>nul
if %errorLevel% neq 0 (
    echo ❌ psutil no instalado
    set MISSING_DEPS=1
)

:: Verificar keyboard
python -c "import keyboard; print('✅ keyboard instalado')" 2>nul
if %errorLevel% neq 0 (
    echo ❌ keyboard no instalado  
    set MISSING_DEPS=1
)

:: Verificar pynput
python -c "import pynput; print(f'✅ pynput {pynput.__version__}')" 2>nul
if %errorLevel% neq 0 (
    echo ❌ pynput no instalado
    set MISSING_DEPS=1
)

:: Verificar pygame
python -c "import pygame; print(f'✅ pygame {pygame.version.ver}')" 2>nul
if %errorLevel% neq 0 (
    echo ❌ pygame no instalado
    set MISSING_DEPS=1
)

echo.

echo 🔐 Verificando permisos...
net session >nul 2>&1
if %errorLevel__ == 0 (
    echo ✅ Ejecutándose como ADMINISTRADOR
    echo    Podrás modificar todos los procesos
) else (
    echo ⚠️  Ejecutándose como usuario normal
    echo    Algunos procesos del sistema podrían no ser modificables
    echo    Para permisos completos: Click derecho → "Ejecutar como administrador"
)
echo.

echo 💻 Verificando PowerShell...
powershell -Command "Get-ExecutionPolicy -Scope CurrentUser" >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('powershell -Command "Get-ExecutionPolicy -Scope CurrentUser"') do (
        if "%%i"=="Restricted" (
            echo ⚠️  PowerShell: Política RESTRINGIDA
            echo    Usa: ejecutar_sin_powershell.bat
            echo    O ejecuta: solucionar_powershell.bat como admin
        ) else (
            echo ✅ PowerShell: Política %%i (OK)
        )
    )
) else (
    echo ❌ Error al verificar PowerShell
)
echo.

echo =====================================================
echo                    RESUMEN
echo =====================================================

if defined MISSING_DEPS (
    echo ❌ FALTAN DEPENDENCIAS
    echo.
    echo 🔧 Para solucionarlo:
    echo    pip install -r requirements.txt
    echo.
    echo O simplemente ejecuta:
    echo    ejecutar_sin_powershell.bat
    echo.
) else (
    echo ✅ TODAS LAS DEPENDENCIAS OK
    echo.
    echo 🚀 El sistema debería funcionar correctamente
    echo.
    echo Para ejecutar:
    echo • ejecutar_sin_powershell.bat (recomendado)
    echo • python affinity_manager.py
    echo.
)

echo ¿Quieres ejecutar la aplicación ahora? (S/N)
set /p respuesta=

if /i "%respuesta%"=="S" (
    echo.
    echo Iniciando aplicación...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    )
    python affinity_manager.py
) else (
    echo.
    echo Diagnóstico completado.
)

echo.
pause
