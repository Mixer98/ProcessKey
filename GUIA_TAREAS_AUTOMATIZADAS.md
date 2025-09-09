# 🎮 Guía de Tareas Automatizadas - Administrador de Afinidad

## 🚀 Nuevas Funcionalidades Agregadas

### ✨ **Tareas Automatizadas con Hotkeys**
Ahora puedes crear **tareas automatizadas** que te permiten alternar entre diferentes configuraciones de afinidad de CPU usando **combinaciones de teclas globales**.

---

## 📖 **Cómo Usar las Tareas Automatizadas**

### **Paso 1: Crear una Nueva Tarea**

1. **Selecciona un proceso** en la pestaña "Control Manual"
2. Haz clic en **"Crear Tarea Automatizada"** 
3. Se abrirá el diálogo de configuración donde puedes:
   - **Nombre de la tarea**: Ej. "Juego - Modo Rendimiento"
   - **Proceso objetivo**: Se detecta automáticamente (ej. "notepad.exe")
   - **Combinación de teclas**: Usa el botón "Grabar" para capturar fácilmente
   - **Afinidad ALTA**: CPUs para máximo rendimiento
   - **Afinidad BAJA**: CPUs para ahorro de energía

### **Paso 2: Configurar las Afinidades**

#### **Afinidad ALTA (Rendimiento Máximo)**
- Selecciona **todas las CPUs** para máximo rendimiento
- O usa **"Última Mitad"** para CPUs más rápidas
- Ideal para: Juegos, renderizado, aplicaciones pesadas

#### **Afinidad BAJA (Ahorro de Energía)**
- Selecciona **menos CPUs** para ahorrar energía
- O usa **"Primera Mitad"** para CPUs básicas
- Ideal para: Navegación, aplicaciones de fondo

### **Paso 3: Asignar Combinación de Teclas**

#### **Métodos para configurar hotkeys:**

1. **Escribir manualmente:**
   - `ctrl+alt+g` (Control + Alt + G)
   - `ctrl+shift+r` (Control + Shift + R)
   - `f1` (Tecla F1)
   - `ctrl+f2` (Control + F2)

2. **Usar el botón "Grabar":**
   - Haz clic en "Grabar"
   - Presiona la combinación deseada
   - Se capturará automáticamente

---

## 🎯 **Ejemplos de Uso Práctico**

### **🎮 Para Gaming:**
```
Tarea: "Juego - Boost de Rendimiento"
Proceso: game.exe
Hotkey: ctrl+alt+g
Afinidad Alta: CPU 0,1,2,3 (todas las CPUs)
Afinidad Baja: CPU 0 (solo una CPU)
```
**Uso:** Presiona `Ctrl+Alt+G` para alternar entre máximo rendimiento y modo normal.

### **🌐 Para Navegador:**
```
Tarea: "Chrome - Modo Eficiencia"
Proceso: chrome.exe
Hotkey: ctrl+alt+c
Afinidad Alta: CPU 2,3 (CPUs rápidas)
Afinidad Baja: CPU 0,1 (CPUs básicas)
```

### **🎵 Para Streaming:**
```
Tarea: "OBS - Control de Recursos"
Proceso: obs64.exe
Hotkey: ctrl+shift+o
Afinidad Alta: CPU 0,1,2,3,4,5 (casi todas)
Afinidad Baja: CPU 0,1 (mínimo necesario)
```

---

## 🔧 **Gestión de Tareas**

### **En la pestaña "Tareas Automatizadas" puedes:**

- **📝 Editar Tarea**: Modificar configuración existente
- **🗑️ Eliminar Tarea**: Quitar tarea y su hotkey
- **🧪 Probar Tarea**: Ejecutar la tarea manualmente
- **👁️ Ver Estado**: Monitorear si las tareas están activas

### **Estados de las Tareas:**
- **✅ Activa**: La tarea está funcionando y el hotkey configurado
- **❌ Error**: Problema con la configuración (revisar proceso o hotkey)
- **⚠️ Advertencia**: El proceso no está en ejecución actualmente

---

## ⚡ **Cómo Funciona el Alternar**

Cuando presionas la combinación de teclas asignada:

1. **El sistema detecta** si el proceso está en ejecución
2. **Verifica la afinidad actual** del proceso
3. **Si está en afinidad alta** → Cambia a afinidad baja
4. **Si está en afinidad baja** → Cambia a afinidad alta
5. **Muestra una notificación** confirmando el cambio

---

## 🛡️ **Consejos de Seguridad**

### **⚠️ Importante:**
- **Ejecuta como administrador** para acceso completo a todos los procesos
- **No modifiques procesos críticos** del sistema sin conocimiento
- **Haz respaldos** antes de configuraciones importantes

### **🎯 Mejores Prácticas:**
- **Usa hotkeys únicas** para evitar conflictos
- **Prueba las tareas** antes del uso intensivo
- **Documenta tus configuraciones** para recordar su propósito

---

## 🔥 **Casos de Uso Avanzados**

### **🏆 Gaming Competitivo:**
- **Hotkey de emergencia** para máximo rendimiento durante partidas importantes
- **Modo streaming** con recursos balanceados entre juego y transmisión

### **💻 Desarrollo/Trabajo:**
- **Compilación rápida** asignando todos los CPUs temporalmente
- **Modo concentración** limitando aplicaciones de fondo

### **🎬 Creación de Contenido:**
- **Renderizado nocturno** con máximo poder de CPU
- **Edición eficiente** balanceando entre editor y previsualización

---

## 📋 **Resolución de Problemas**

### **❌ El hotkey no funciona:**
- Verifica que no esté en uso por otra aplicación
- Ejecuta como administrador
- Revisa el estado en la pestaña de tareas

### **❌ El proceso no se encuentra:**
- Verifica que el nombre del proceso sea exacto (ej. "notepad.exe")
- El proceso debe estar en ejecución para funcionar

### **❌ Acceso denegado:**
- Ejecuta la aplicación como administrador
- Algunos procesos del sistema requieren permisos especiales

---

## 🎉 **¡Disfruta del Control Total!**

Con las **tareas automatizadas** tienes el poder de optimizar tu sistema al vuelo. Experimenta con diferentes configuraciones y encuentra la combinación perfecta para tu flujo de trabajo.

**¡Tu productividad y rendimiento nunca habían sido tan fáciles de controlar!** 🚀
