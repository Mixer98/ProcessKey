@echo off
chcp 65001 >nul
title Compilador - Administrador de Afinidad de Procesos
color 0A

echo.
echo ========================================
echo  🚀 COMPILADOR DE EJECUTABLE
echo  Administrador de Afinidad de Procesos
echo ========================================
echo.

echo 📋 Verificando estructura del proyecto...

if not exist "src\main.py" (
    echo ❌ ERROR: No se encuentra src\main.py
    echo    Asegúrate de ejecutar este archivo desde dist_project
    pause
    exit /b 1
)

echo ✅ Estructura verificada correctamente
echo.

echo 📦 Instalando PyInstaller (si es necesario)...
pip install pyinstaller >nul 2>&1

echo.
echo 🔨 Iniciando compilación...
echo    Esto puede tomar varios minutos...
echo.

cd src

pyinstaller ^
    --onefile ^
    --windowed ^
    --name=AdministradorAfinidad ^
    --distpath=../exe ^
    --workpath=../build ^
    --specpath=../ ^
    --add-data=task_manager.py;. ^
    --add-data=ui_components.py;. ^
    --hidden-import=pygame ^
    --hidden-import=pynput ^
    --hidden-import=psutil ^
    --hidden-import=keyboard ^
    --hidden-import=tkinter ^
    --hidden-import=threading ^
    --hidden-import=json ^
    --hidden-import=ctypes ^
    --hidden-import=winsound ^
    --clean ^
    main.py

cd ..

echo.
if exist "exe\AdministradorAfinidad.exe" (
    echo ✅ ¡COMPILACIÓN EXITOSA!
    echo.
    echo 📂 Ejecutable creado en: exe\AdministradorAfinidad.exe
    
    for %%I in ("exe\AdministradorAfinidad.exe") do (
        set /a size_mb=%%~zI/1048576
    )
    echo 📊 Tamaño: %size_mb% MB aproximadamente
    echo.
    
    echo 📁 Copiando archivos de configuración...
    if exist "config\automated_tasks.json" (
        copy "config\automated_tasks.json" "exe\" >nul 2>&1
        echo ✅ automated_tasks.json copiado
    )
    
    echo.
    echo 🎉 ¡PROCESO COMPLETADO!
    echo 💡 Para usar el ejecutable:
    echo    1. Ve a la carpeta 'exe'
    echo    2. Ejecuta AdministradorAfinidad.exe como administrador
    echo    3. ¡Disfruta tu aplicación portable!
    echo.
    
    set /p open="¿Abrir carpeta exe? (s/n): "
    if /i "%open%"=="s" explorer exe
    
) else (
    echo ❌ ERROR: No se pudo crear el ejecutable
    echo    Revisa los mensajes de error anteriores
    echo.
)

echo.
echo Presiona cualquier tecla para continuar...
pause >nul
