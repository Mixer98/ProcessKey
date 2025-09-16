"""
Utilidades para el manejo de iconos en la aplicación
Reemplaza emojis por iconos de archivos PNG
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class IconManager:
    """Gestor de iconos para la aplicación"""
    
    def __init__(self):
        # Buscar la ruta correcta de iconos
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_icons = os.path.join(current_dir, "assets", "icons")
        parent_icons = os.path.join(os.path.dirname(current_dir), "assets", "icons")
        
        if os.path.exists(src_icons):
            self.icons_path = src_icons
        elif os.path.exists(parent_icons):
            self.icons_path = parent_icons
        else:
            self.icons_path = "assets/icons"  # fallback
            
        # Mapeo de emojis a archivos de iconos
        self.emoji_to_icon = {
            # Iconos principales de la aplicación
            "🚀": "Rocket.png",           # Afinidad ALTA aplicada / Instalación
            "💚": "GrennHeart.png",       # Afinidad BAJA aplicada / Eficiencia (usando GrennHeart.png que está en la lista)
            "❌": "CrossMark.png",        # Error / Deseleccionar todas
            "⚠️": "WarningSign.png",      # Advertencia / Consideraciones
            "✅": "CheckMark.png",        # Éxito / Seleccionar todas
            "ℹ️": "Information.png",      # Información general
            "🎯": "Target.png",           # Control Manual / Objetivo / Notificaciones
            
            # Iconos de interfaz de usuario
            "👁️": "Eye.png",             # Mostrar/Ocultar Log / Visibilidad
            "🧪": "TestTube.png",         # Prueba de captura / Testing
            "🖥️": "DesktopComputer.png",  # Administrador de Afinidad (título principal)
            "📝": "Memo.png",             # Registro de Actividad / Nombres de tareas
            "📋": "Clipboard.png",        # Procesos en Ejecución / Listas
            "📊": "BarChart.png",         # Información del Proceso / Estado / Estadísticas
            "⚙️": "Gear.png",             # Control de Afinidad de CPU / Configuración
            "🔧": "Wrench.png",           # Seleccionar CPUs / Crear Tarea / Herramientas / Uso
            "🎛️": "ControlKnobs.png",     # Controles de Tareas
            "✏️": "Pencil.png",           # Editar Tarea
            "🗑️": "Wastebasket.png",      # Limpiar Log / Eliminar Tarea
            "⌨️": "Keyboard.png",         # Tecla Rápida / Hotkeys
            
            # Iconos de estado del sistema
            "🟢": "green.png",            # Funcionando / Activo / Saludable / Recuperado
            "🔴": "red.png",              # Detenido / Inactivo / Error
            "🟡": "yelow.png",            # Problemático / Advertencia (usando yelow.png que está en la lista)
            "💀": "Skull.png",            # Fallido completamente
            "⚪": "White.png",            # Desconocido / Estado neutral
            "🔄": "Counterclockwise.png", # Intento de recuperación / Recarga
            
            # Iconos adicionales que aparecen en el código
            "⚡": "Rocket.png",           # Para tareas automatizadas (usando Rocket)
            "🔘": "green.png",           # Estado del sistema (usando verde)
            "💡": "Information.png",      # Información/consejos (usando Information)
            "📌": "Target.png",          # Minimizar a bandeja (usando Target)
            "🔔": "Information.png",      # Alertas (usando Information)
            "🕒": "Information.png",      # Tiempo/última activación (usando Information)
            "🔢": "Information.png",      # Contador (usando Information)
            "📁": "Clipboard.png",       # Examinar archivos (usando Clipboard)
            "💾": "Gear.png",            # Guardar configuración (usando Gear)
            "🏭": "Gear.png",            # Restaurar por defecto (usando Gear)
            "▶️": "green.png",           # Iniciar servicio (usando verde)
            "🔍": "Eye.png",             # Sistema de monitoreo (usando Eye)
        }
        
        # Cache de imágenes cargadas
        self.icon_cache = {}
        
        # Directorio de iconos
        self.icons_dir = "assets/icons"
        
    def get_icon_path(self, emoji: str) -> str:
        """Obtiene la ruta del icono correspondiente al emoji"""
        icon_file = self.emoji_to_icon.get(emoji)
        if icon_file:
            return os.path.join(self.icons_path, icon_file)
        return None
    
    def load_icon(self, emoji: str, size: tuple = (16, 16)) -> ImageTk.PhotoImage:
        """Carga un icono desde archivo y lo redimensiona"""
        cache_key = f"{emoji}_{size[0]}x{size[1]}"
        
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        icon_path = self.get_icon_path(emoji)
        if icon_path and os.path.exists(icon_path):
            try:
                # Cargar y redimensionar imagen
                image = Image.open(icon_path)
                image = image.resize(size, Image.Resampling.LANCZOS)
                
                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Cachear resultado
                self.icon_cache[cache_key] = photo
                
                return photo
            except Exception as e:
                print(f"Error cargando icono {icon_path}: {e}")
                return None
        return None
    
    def replace_emoji_with_icon(self, text: str, size: tuple = (16, 16)) -> tuple:
        """
        Reemplaza emojis en el texto con iconos
        Retorna (texto_sin_emoji, lista_de_iconos)
        """
        icons = []
        clean_text = text
        
        for emoji in self.emoji_to_icon.keys():
            if emoji in text:
                icon = self.load_icon(emoji, size)
                if icon:
                    icons.append((emoji, icon))
                    # Remover el emoji del texto (opcional)
                    clean_text = clean_text.replace(emoji, "")
        
        return clean_text.strip(), icons
    
    def get_icon_for_emoji(self, emoji: str, size: tuple = (16, 16)) -> ImageTk.PhotoImage:
        """Obtiene un icono específico para un emoji"""
        return self.load_icon(emoji, size)

# Instancia global del gestor de iconos
icon_manager = IconManager()

def create_labeled_button(parent, text: str, command=None, **kwargs) -> ttk.Button:
    """
    Crea un botón que puede mostrar iconos junto al texto
    """
    # Extraer emoji del texto si existe
    for emoji in icon_manager.emoji_to_icon.keys():
        if emoji in text:
            icon = icon_manager.get_icon_for_emoji(emoji, (16, 16))
            if icon:
                # Crear botón con icono
                clean_text = text.replace(emoji, "").strip()
                btn = ttk.Button(parent, text=clean_text, image=icon, compound="left", 
                               command=command, **kwargs)
                # Mantener referencia a la imagen
                btn.image = icon
                return btn
    
    # Si no hay emoji o no se puede cargar el icono, crear botón normal
    return ttk.Button(parent, text=text, command=command, **kwargs)

def create_labeled_label(parent, text: str, **kwargs) -> ttk.Label:
    """
    Crea una etiqueta que puede mostrar iconos junto al texto
    """
    # Extraer emoji del texto si existe
    for emoji in icon_manager.emoji_to_icon.keys():
        if emoji in text:
            icon = icon_manager.get_icon_for_emoji(emoji, (16, 16))
            if icon:
                # Crear label con icono
                clean_text = text.replace(emoji, "").strip()
                lbl = ttk.Label(parent, text=clean_text, image=icon, compound="left", **kwargs)
                # Mantener referencia a la imagen
                lbl.image = icon
                return lbl
    
    # Si no hay emoji o no se puede cargar el icono, crear label normal
    return ttk.Label(parent, text=text, **kwargs)
