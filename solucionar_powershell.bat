@echo off
chcp 65001 >nul
echo =====================================================
echo        SOLUCIONADOR DE PROBLEMAS DE POWERSHELL
echo =====================================================
echo.
echo Este script configura PowerShell para permitir 
echo la ejecución de scripts de entornos virtuales.
echo.

:: Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ ESTE SCRIPT NECESITA PERMISOS DE ADMINISTRADOR
    echo.
    echo Para solucionarlo:
    echo 1. Click derecho en este archivo
    echo 2. Selecciona "Ejecutar como administrador"
    echo.
    echo Alternativamente, puedes usar: ejecutar_sin_powershell.bat
    echo (que no requiere permisos de administrador)
    echo.
    pause
    exit /b 1
)

echo ✓ Ejecutándose como administrador
echo.
echo Configurando PowerShell...

:: Configurar política de ejecución para el usuario actual
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

if %errorLevel% == 0 (
    echo ✓ PowerShell configurado correctamente
    echo.
    echo Ahora puedes usar PowerShell normalmente:
    echo   .\.venv\Scripts\Activate.ps1
    echo   python affinity_manager.py
    echo.
    
    echo ¿Quieres ejecutar la aplicación ahora? (S/N)
    set /p respuesta=
    
    if /i "%respuesta%"=="S" (
        echo.
        echo Ejecutando aplicación...
        cd /d "%~dp0"
        
        if exist ".venv\Scripts\Activate.ps1" (
            powershell -Command "& '.\.venv\Scripts\Activate.ps1'; python affinity_manager.py"
        ) else (
            python affinity_manager.py
        )
    )
) else (
    echo ✗ Error al configurar PowerShell
    echo.
    echo Usa el archivo: ejecutar_sin_powershell.bat
    echo como alternativa.
)

echo.
echo =====================================================
pause
