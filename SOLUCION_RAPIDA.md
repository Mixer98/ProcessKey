# Guía Rápida: Solución de Problemas de PowerShell

## 🔥 **SOLUCIÓN INMEDIATA** 🔥

### **Opción 1: La Más Fácil (Sin Administrador)**
Haz **doble click** en: `ejecutar_sin_powershell.bat`

### **Opción 2: Solución Permanente (Requiere Administrador)**
1. **Click derecho** en: `solucionar_powershell.bat`
2. Selecciona: **"Ejecutar como administrador"**

---

## ¿Por Qué Ocurre Este Error?

Windows bloquea la ejecución de scripts de PowerShell por seguridad. Esto afecta los entornos virtuales de Python.

## Todas las Soluciones Disponibles

### 🟢 **Método 1: Script Automático (Recomendado)**
```cmd
ejecutar_sin_powershell.bat
```
- ✅ No requiere administrador
- ✅ Funciona inmediatamente
- ✅ Instala dependencias si faltan

### 🟡 **Método 2: Configurar PowerShell (Una sola vez)**
```cmd
solucionar_powershell.bat (como administrador)
```
- ✅ Solución permanente
- ⚠️ Requiere permisos de administrador
- ✅ PowerShell funcionará normalmente después

### 🔵 **Método 3: Comandos Manuales en CMD**
```cmd
cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
.venv\Scripts\activate.bat
python affinity_manager.py
```

### 🟠 **Método 4: PowerShell Manual (Como Administrador)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
.\.venv\Scripts\Activate.ps1
python affinity_manager.py
```

### 🔴 **Método 5: Sin Entorno Virtual**
```cmd
cd "C:\Users\Administrator\Documents\Carpeta De Dessarrollo\afinity key"
python affinity_manager.py
```
- ⚠️ Solo si tienes las librerías instaladas globalmente

---

## ⭐ **Recomendación**

1. **Primera vez**: Usa `ejecutar_sin_powershell.bat`
2. **Si quieres usar PowerShell siempre**: Ejecuta `solucionar_powershell.bat` como administrador

## 🛠️ **Dependencias Necesarias**

Si Python dice que faltan librerías:
```cmd
pip install psutil keyboard pynput pygame numpy
```

---

## 📞 **¿Necesitas Ayuda?**

Si ningún método funciona:

1. Verifica que Python esté instalado: `python --version`
2. Verifica que pip funcione: `pip --version`
3. Reinstala las dependencias: `pip install -r requirements.txt`

**¡El programa debería funcionar con cualquiera de estos métodos!** 🎯
