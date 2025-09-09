# Administrador de Afinidad de Procesos - Launcher PowerShell
# Verificar y ejecutar con permisos apropiados

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "    Administrador de Afinidad de Procesos" -ForegroundColor Cyan  
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($isAdmin) {
    Write-Host "✓ Ejecutándose como administrador" -ForegroundColor Green
} else {
    Write-Host "⚠ No se detectaron permisos de administrador" -ForegroundColor Yellow
    Write-Host "  Para acceso completo a todos los procesos del sistema," -ForegroundColor Yellow
    Write-Host "  ejecute PowerShell como administrador y vuelva a ejecutar este script." -ForegroundColor Yellow
}

Write-Host ""

# Verificar si Python está disponible
try {
    $pythonVersion = & python --version 2>$null
    if ($pythonVersion) {
        Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Python no encontrado. Asegúrese de que Python esté instalado y en el PATH." -ForegroundColor Red
    pause
    exit 1
}

# Activar entorno virtual si existe
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    if ($?) {
        Write-Host "✓ Entorno virtual activado" -ForegroundColor Green
    }
}

# Verificar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
try {
    & python -c "import psutil; print('✓ psutil disponible')" 2>$null
    if (-not $?) {
        Write-Host "Instalando dependencias..." -ForegroundColor Yellow
        & pip install -r requirements.txt
    }
} catch {
    Write-Host "❌ Error al verificar dependencias" -ForegroundColor Red
}

Write-Host ""
Write-Host "Iniciando aplicación..." -ForegroundColor Cyan
Write-Host ""

# Ejecutar la aplicación
try {
    & python affinity_manager.py
} catch {
    Write-Host "❌ Error al ejecutar la aplicación: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "La aplicación se ha cerrado." -ForegroundColor Gray
Read-Host "Presione Enter para continuar"
