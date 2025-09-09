@echo off
echo =====================================================
echo    Administrador de Afinidad de Procesos
echo =====================================================
echo.
echo Verificando permisos de administrador...

:: Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Ejecutandose como administrador
    echo.
) else (
    echo ✗ No se detectaron permisos de administrador
    echo   Para acceso completo, ejecute este archivo como administrador
    echo.
)

echo Iniciando aplicacion...
echo.

:: Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call .venv\Scripts\activate.bat
)

:: Ejecutar la aplicacion
python affinity_manager.py

echo.
echo La aplicacion se ha cerrado.
pause
