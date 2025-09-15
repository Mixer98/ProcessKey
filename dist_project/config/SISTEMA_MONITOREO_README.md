# Sistema de Monitoreo y Recuperación Automática

## Descripción
El nuevo sistema de monitoreo detecta automáticamente cuando el servicio de captura de teclas deja de funcionar y trata de recuperarlo sin necesidad de reiniciar la aplicación.

## Características Principales

### 🔍 Monitoreo Continuo
- **Detección Automática**: El sistema verifica constantemente si las teclas se están capturando correctamente
- **Timeout Configurable**: Puedes establecer el tiempo máximo sin captura antes de activar la recuperación (por defecto: 5 minutos)
- **Estado de Salud**: Muestra el estado actual del servicio en tiempo real

### 🔧 Recuperación Automática
- **Múltiples Métodos**: El sistema intenta diferentes estrategias de recuperación:
  1. Reinicio del servicio de hotkeys
  2. Reconfiguración del listener global
  3. Reset completo del sistema de captura
- **Límite de Intentos**: Máximo 3 intentos automáticos para evitar bucles infinitos
- **Recuperación Manual**: Botón para forzar una prueba de recuperación

### 📊 Información en Tiempo Real
- **Tiempo sin Captura**: Muestra cuánto tiempo ha pasado desde la última tecla detectada
- **Intentos de Recuperación**: Contador de intentos automáticos realizados
- **Última Recuperación**: Timestamp de la última recuperación exitosa
- **Estado de Salud**: Indicador visual del estado del sistema

## Configuración

### Pestaña "Servicio de Hotkeys"
En la nueva sección "Sistema de Monitoreo y Recuperación" encontrarás:

1. **Timeout de Monitoreo**: Tiempo en minutos antes de activar la recuperación automática
2. **Recuperación Automática**: Checkbox para activar/desactivar la recuperación automática
3. **Botones de Control**:
   - `🔧 Prueba Manual`: Ejecuta manualmente una prueba de recuperación
   - `🔄 Reset Contador`: Resetea el contador de intentos de recuperación
   - `⚡ Aplicar Timeout`: Aplica el nuevo valor de timeout
   - `📊 Ver Estado`: Actualiza manualmente la información del estado

### Archivo de Configuración
La configuración se guarda en `hotkey_service_config.json`:

```json
{
  "capture_delay": "100",
  "debug_mode": false,
  "service_enabled": true,
  "monitoring_timeout": "5",
  "auto_recovery_enabled": true,
  "max_recovery_attempts": 3
}
```

## Estados del Sistema

### 🟢 Saludable
- El sistema está funcionando correctamente
- Las teclas se capturan sin problemas

### 🟡 Problemático
- Se detectaron problemas menores
- El sistema está intentando recuperarse

### 🔴 Error
- Error crítico en el sistema de captura
- Se requiere intervención manual

### ✅ Recuperado
- El sistema se recuperó exitosamente de un problema
- Funcionando normalmente después de la recuperación

### ❌ Fallo Total
- Se agotaron todos los intentos de recuperación automática
- Se requiere reinicio manual del servicio o la aplicación

## Solución de Problemas

### Si el sistema no detecta teclas:
1. Verifica que la recuperación automática esté activada
2. Usa el botón "Prueba Manual" para forzar una recuperación
3. Si continúa fallando, reinicia el servicio manualmente
4. Como último recurso, reinicia la aplicación

### Si hay demasiados intentos de recuperación:
1. Aumenta el valor del timeout de monitoreo
2. Verifica que no hay conflictos con otras aplicaciones
3. Ejecuta la aplicación como administrador

### Para depuración:
1. Activa el "Modo de depuración" en la configuración avanzada
2. Revisa el log para mensajes detallados
3. Usa el botón "Probar Captura" para verificar el funcionamiento

## Beneficios

- **Mayor Estabilidad**: Reduce la necesidad de reiniciar la aplicación
- **Experiencia Mejorada**: Los hotkeys siguen funcionando incluso después de problemas temporales
- **Diagnóstico Fácil**: Información clara sobre el estado del sistema
- **Configuración Flexible**: Ajusta el comportamiento según tus necesidades
