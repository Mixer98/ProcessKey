# Administrador de Afinidad de Procesos

Una aplicación de escritorio con interfaz gráfica para gestionar la afinidad de CPU de procesos en Windows.

## 🌟 Características

### **Control Manual**
- **Interfaz gráfica intuitiva**: Fácil de usar con tkinter y **iconos PNG profesionales**
- **Lista de procesos en tiempo real**: Visualiza todos los procesos activos con información de CPU y memoria
- **Control granular de afinidad**: Selecciona qué CPUs puede usar cada proceso
- **Verificación de permisos**: Detecta automáticamente si se ejecuta como administrador
- **Sistema de iconos**: Reemplaza emojis con iconos PNG de alta calidad para mejor experiencia visual

### **🆕 Tareas Automatizadas (NUEVO)**
- **Hotkeys globales**: Asigna combinaciones de teclas para alternar afinidad al vuelo
- **Perfiles de rendimiento**: Define configuraciones de afinidad alta (rendimiento) y baja (eficiencia)
- **Alternado inteligente**: Cambia automáticamente entre modos según la situación
- **Grabación de teclas**: Captura fácilmente las combinaciones de teclas deseadas
- **Gestión de tareas**: Crear, editar, eliminar y probar tareas automatizadas

### **Sistema**
- **Registro de actividad**: Log detallado de todas las operaciones realizadas
- **Actualización automática**: Refrescado de la lista de procesos
- **Manejo de errores**: Control robusto de errores y excepciones
- **Persistencia**: Las tareas se guardan automáticamente y se cargan al inicio

## 🚀 **Instalación y Ejecución**

### **INICIO SÚPER RÁPIDO** ⚡
1. **Descarga/clona el proyecto**
2. **Haz doble click en**: `INICIO.bat` 
3. **Selecciona opción 1**
4. **¡Listo!** 🎉

### **INICIO RÁPIDO ALTERNATIVO** 
1. **Haz doble click en**: `ejecutar_sin_powershell.bat`
2. **¡Funciona inmediatamente!** 🎉

> ⚠️ **¿Problemas?** 
> - 🔧 Haz click en: `diagnostico.bat`
> - 📖 Lee: [Solución Rápida](SOLUCION_RAPIDA.md)

### Prerrequisitos
- Python 3.7 o superior
- Windows (la aplicación está optimizada para Windows)

### **Métodos de Ejecución** 🎯

#### **🥇 Método 1: Automático (Más Fácil)**
```cmd
ejecutar_sin_powershell.bat
```
- ✅ **Sin configuración adicional**
- ✅ **Instala dependencias automáticamente**
- ✅ **Evita problemas de PowerShell**

#### **🥈 Método 2: Configurar PowerShell (Una sola vez)**
Como **administrador**:
```cmd
solucionar_powershell.bat
```
Después podrás usar PowerShell normalmente.

#### **🥉 Método 3: Manual**
```cmd
# Clonar proyecto
git clone [URL_DEL_REPOSITORIO]
cd "afinity key"

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python affinity_manager.py
```

## 🔧 **Uso y Ejecución**

### **⚡ Inicio Rápido**
1. **Doble click** en `ejecutar_sin_powershell.bat`
2. **¡Ya está funcionando!**

### **🛡️ Como Administrador (Recomendado)**
Para modificar **todos** los procesos del sistema:
- **Click derecho** en `ejecutar_sin_powershell.bat`
- **"Ejecutar como administrador"**

## 📖 Guía de Uso

### Paso 1: Seleccionar un Proceso
1. Al iniciar la aplicación, verás una lista de todos los procesos en ejecución
2. La lista muestra: PID, Nombre del proceso, % de CPU y uso de memoria
3. Haz clic en cualquier proceso para seleccionarlo

### Paso 2: Ver Afinidad Actual
- Una vez seleccionado un proceso, verás su afinidad actual en el panel derecho
- Se mostrará qué CPUs puede usar actualmente el proceso

### Paso 3: Modificar Afinidad
1. En la sección "Seleccionar CPUs", marca las casillas de las CPUs que quieres asignar
2. Usa los botones "Seleccionar Todas" o "Deseleccionar Todas" para facilitar la selección
3. Haz clic en "Aplicar Afinidad" para aplicar los cambios

### Funciones Adicionales
- **Actualizar Lista**: Refresca la lista de procesos
- **Registro de Actividad**: Consulta el log en la parte inferior para ver todas las operaciones

### 🆕 Tareas Automatizadas
1. **Crear Tarea**: Selecciona un proceso y haz clic en "Crear Tarea Automatizada"
2. **Configurar Perfiles**: Define afinidad alta (rendimiento) y baja (eficiencia)
3. **Asignar Hotkey**: Usa el botón "Grabar" o escribe la combinación (ej: ctrl+alt+g)
4. **Usar en Tiempo Real**: Presiona la combinación asignada para alternar entre modos
5. **Gestionar**: Edita, elimina o prueba tus tareas en la pestaña correspondiente

**Ejemplos de Uso:**
- **Gaming**: `Ctrl+Alt+G` para alternar entre rendimiento máximo y modo normal
- **Streaming**: `Ctrl+Alt+S` para balancear recursos entre OBS y otras aplicaciones  
- **Trabajo**: `Ctrl+Alt+W` para optimizar aplicaciones de productividad

## ⚠️ Consideraciones de Seguridad

### Permisos de Administrador
- **Sin permisos de admin**: Solo podrás modificar procesos de tu usuario
- **Con permisos de admin**: Acceso completo a todos los procesos del sistema

### Procesos Críticos del Sistema
- Ten cuidado al modificar procesos del sistema
- Cambiar la afinidad de procesos críticos puede afectar el rendimiento
- Se recomienda hacer respaldos o crear puntos de restauración

## 🛠️ Características Técnicas

### Dependencias
- **psutil**: Para el manejo de procesos y información del sistema
- **tkinter**: Para la interfaz gráfica (incluido con Python)
- **keyboard**: Para captura de hotkeys globales
- **pynput**: Para monitoreo avanzado de teclado

### Compatibilidad
- **Sistema Operativo**: Windows (optimizado)
- **Python**: 3.7+
- **Arquitectura**: x64, x86

### Limitaciones
- Requiere permisos de administrador para acceso completo
- Algunos procesos protegidos pueden no ser modificables
- La aplicación está optimizada para Windows

## 🐛 Solución de Problemas

### Error: "Acceso Denegado"
- **Solución**: Ejecutar la aplicación como administrador
- **Alternativa**: Solo modificar procesos de tu usuario

### Error: "El proceso ya no existe"
- **Causa**: El proceso terminó mientras intentabas modificar su afinidad
- **Solución**: Actualizar la lista de procesos y seleccionar otro

### La aplicación no inicia
- Verificar que Python esté instalado correctamente
- Instalar las dependencias: `pip install -r requirements.txt`
- Verificar compatibilidad de versión de Python

## 📝 Registro de Cambios

### Versión 1.0.0
- Implementación inicial
- Interfaz gráfica completa
- Gestión de afinidad de procesos
- Sistema de logging
- Verificación de permisos

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚡ Rendimiento y Optimización

### Consejos para el Uso Óptimo
- **Para gaming**: Asigna juegos a CPUs específicas para mejor rendimiento
- **Para renderizado**: Usa todas las CPUs disponibles para máxima potencia
- **Para multitarea**: Distribuye aplicaciones pesadas en diferentes CPUs

### Monitoreo
- Usa el Task Manager de Windows junto con esta herramienta para monitorear el impacto
- Observa el uso de CPU antes y después de aplicar cambios de afinidad

---

**Nota**: Esta herramienta es para usuarios avanzados que entienden las implicaciones de modificar la afinidad de procesos. Úsala bajo tu propio riesgo.

### **Sistema de Iconos**
- **Iconos PNG de alta calidad**: Reemplaza emojis con archivos PNG ubicados en `assets/icons/`
- **Sistema de fallback**: Si los iconos no están disponibles, usa emojis automáticamente
- **Cache inteligente**: Optimiza el rendimiento cargando iconos una sola vez
- **Compatibilidad total**: Funciona sin modificar la lógica existente de la aplicación
- **Fácil personalización**: Cambia los iconos reemplazando archivos en `assets/icons/`