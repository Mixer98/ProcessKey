@echo off
chcp 65001 >nul
title Administrador de Afinidad de CPU - Menú Principal

:menu
cls
echo =====================================================
echo     🖥️  ADMINISTRADOR DE AFINIDAD DE CPU  🖥️
echo =====================================================
echo.
echo Selecciona una opción:
echo.
echo  1️⃣  EJECUTAR APLICACIÓN (Automático)
echo  2️⃣  Ejecutar como Administrador  
echo  3️⃣  Solucionar problema de PowerShell
echo  4️⃣  Diagnóstico del sistema
echo  5️⃣  Instalar/Actualizar dependencias
echo  6️⃣  Crear entorno virtual
echo  7️⃣  Ver documentación
echo  8️⃣  Ayuda rápida
echo  9️⃣  Salir
echo.
echo =====================================================

set /p opcion="Ingresa el número de tu opción: "

if "%opcion%"=="1" goto ejecutar
if "%opcion%"=="2" goto ejecutar_admin
if "%opcion%"=="3" goto solucionar_ps
if "%opcion%"=="4" goto diagnostico
if "%opcion%"=="5" goto instalar_deps
if "%opcion%"=="6" goto crear_venv
if "%opcion%"=="7" goto documentacion
if "%opcion%"=="8" goto ayuda
if "%opcion%"=="9" goto salir

echo Opción no válida. Presiona cualquier tecla para continuar...
pause >nul
goto menu

:ejecutar
cls
echo =====================================================
echo              EJECUTANDO APLICACIÓN
echo =====================================================
echo.
call ejecutar_sin_powershell.bat
pause
goto menu

:ejecutar_admin
cls
echo =====================================================
echo       EJECUTANDO COMO ADMINISTRADOR
echo =====================================================
echo.
echo Se abrirá una ventana con permisos elevados...
echo.
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && ejecutar_sin_powershell.bat && pause' -Verb RunAs"
echo.
echo Si no se abrió la ventana, ejecuta manualmente:
echo "ejecutar_sin_powershell.bat" como administrador
echo.
pause
goto menu

:solucionar_ps
cls
echo =====================================================
echo        SOLUCIONANDO PROBLEMA POWERSHELL
echo =====================================================
echo.
echo Se abrirá una ventana con permisos de administrador...
echo.
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && solucionar_powershell.bat && pause' -Verb RunAs"
echo.
echo Si no funcionó, lee: SOLUCION_RAPIDA.md
echo.
pause
goto menu

:diagnostico
cls
echo =====================================================
echo           EJECUTANDO DIAGNÓSTICO
echo =====================================================
echo.
call diagnostico.bat
pause
goto menu

:instalar_deps
cls
echo =====================================================
echo        INSTALANDO DEPENDENCIAS
echo =====================================================
echo.
echo Verificando pip...
pip --version
echo.
echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
echo.
echo ✅ Instalación completada.
echo.
pause
goto menu

:crear_venv
cls
echo =====================================================
echo        CREANDO ENTORNO VIRTUAL
echo =====================================================
echo.
if exist ".venv\" (
    echo ⚠️  El entorno virtual ya existe.
    echo ¿Quieres recrearlo? (S/N)
    set /p respuesta=
    if /i "!respuesta!"=="S" (
        echo Eliminando entorno actual...
        rmdir /s /q .venv
    ) else (
        goto menu
    )
)

echo Creando entorno virtual...
python -m venv .venv

if exist ".venv\" (
    echo ✅ Entorno virtual creado exitosamente.
    echo.
    echo Activando y instalando dependencias...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo.
    echo ✅ Todo configurado correctamente.
) else (
    echo ❌ Error al crear el entorno virtual.
    echo Verifica que Python esté instalado correctamente.
)
echo.
pause
goto menu

:documentacion
cls
echo =====================================================
echo             DOCUMENTACIÓN DISPONIBLE
echo =====================================================
echo.
echo 📖 Archivos de documentación:
echo.
if exist "README.md" echo • README.md - Guía principal
if exist "SOLUCION_RAPIDA.md" echo • SOLUCION_RAPIDA.md - Soluciones rápidas
if exist "SOLUCION_SCRIPTS.md" echo • SOLUCION_SCRIPTS.md - Problemas de PowerShell  
if exist "NUEVAS_FUNCIONALIDADES.md" echo • NUEVAS_FUNCIONALIDADES.md - Nuevas características
if exist "NUEVAS_MEJORAS.md" echo • NUEVAS_MEJORAS.md - Mejoras implementadas
echo.
echo 🌐 Para ver los archivos, ábrelos con un editor de texto
echo    o navegador web (si tienen formato Markdown).
echo.
pause
goto menu

:ayuda
cls
echo =====================================================
echo                 AYUDA RÁPIDA
echo =====================================================
echo.
echo 🚀 PROBLEMA MÁS COMÚN: Error de PowerShell
echo    SOLUCIÓN: Usa la opción 1 (Ejecutar Automático)
echo.
echo 🛠️  PROBLEMA: Python no encontrado  
echo    SOLUCIÓN: Instala Python desde python.org
echo.
echo 📦 PROBLEMA: Faltan dependencias
echo    SOLUCIÓN: Usa la opción 5 (Instalar dependencias)
echo.
echo 🔐 PROBLEMA: No puede modificar algunos procesos
echo    SOLUCIÓN: Usa la opción 2 (Como administrador)
echo.
echo 💡 CONSEJO: Si tienes dudas, ejecuta la opción 4
echo    (Diagnóstico) para ver el estado completo.
echo.
echo 📞 MÁS AYUDA: Lee SOLUCION_RAPIDA.md
echo.
pause
goto menu

:salir
cls
echo =====================================================
echo              ¡Hasta la próxima! 👋
echo =====================================================
echo.
echo Gracias por usar el Administrador de Afinidad de CPU
echo.
timeout /t 2 >nul
exit
