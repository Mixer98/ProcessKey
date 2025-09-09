# Solución: Error de Ejecución de Scripts en PowerShell

## El Problema
PowerShell tiene deshabilitada la ejecución de scripts por seguridad. Esto impide activar el entorno virtual.

## Soluciones Disponibles

### Opción 1: Habilitar Scripts Temporalmente (Recomendado)

1. **Abrir PowerShell como Administrador:**
   - Busca "PowerShell" en el menú inicio
   - Click derecho → "Ejecutar como administrador"

2. **Ejecutar este comando:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Confirmar cuando te pregunte (escribir 'S' o 'Y')**

4. **Ahora ya puedes activar el entorno virtual:**
   ```powershell
   cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
   .\.venv\Scripts\Activate.ps1
   python affinity_manager.py
   ```

### Opción 2: Ejecutar Sin Entorno Virtual (Rápido)

Si tienes Python y las librerías instaladas globalmente:

```cmd
cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
python affinity_manager.py
```

### Opción 3: Usar CMD en lugar de PowerShell

```cmd
cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
.venv\Scripts\activate.bat
python affinity_manager.py
```

### Opción 4: Script de Bypass Automático

Usar el archivo `run_direct.bat` que te voy a crear.

## ¿Qué Opción Elegir?

- **Opción 1**: La más completa y recomendada
- **Opción 2**: Si quieres probar rápido
- **Opción 3**: Alternative simple 
- **Opción 4**: La más fácil (un solo click)

## Nota de Seguridad
La Opción 1 solo permite scripts firmados y locales. Es seguro para desarrollo.
