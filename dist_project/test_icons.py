#!/usr/bin/env python3
"""
Script de ejemplo para demostrar el uso del sistema de iconos
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio src al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from icon_utils import icon_manager, create_labeled_button, create_labeled_label

def test_icon_system():
    """Prueba el sistema de iconos con algunos ejemplos"""
    
    root = tk.Tk()
    root.title("Prueba del Sistema de Iconos")
    root.geometry("600x400")
    
    # Frame principal
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    title_label = create_labeled_label(main_frame, "🖥️ Prueba del Sistema de Iconos", 
                                     font=('Arial', 16, 'bold'))
    title_label.pack(pady=(0, 20))
    
    # Frame para botones
    buttons_frame = ttk.LabelFrame(main_frame, text="Botones con Iconos", padding="10")
    buttons_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Primera fila de botones
    row1_frame = ttk.Frame(buttons_frame)
    row1_frame.pack(fill=tk.X, pady=(0, 10))
    
    create_labeled_button(row1_frame, "🚀 Aplicar Afinidad", 
                         command=lambda: print("Aplicar afinidad")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row1_frame, "✅ Seleccionar Todas", 
                         command=lambda: print("Seleccionar todas")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row1_frame, "❌ Deseleccionar Todas", 
                         command=lambda: print("Deseleccionar todas")).pack(side=tk.LEFT)
    
    # Segunda fila de botones
    row2_frame = ttk.Frame(buttons_frame)
    row2_frame.pack(fill=tk.X, pady=(0, 10))
    
    create_labeled_button(row2_frame, "🔧 Crear Tarea", 
                         command=lambda: print("Crear tarea")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row2_frame, "✏️ Editar Tarea", 
                         command=lambda: print("Editar tarea")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row2_frame, "🗑️ Eliminar Tarea", 
                         command=lambda: print("Eliminar tarea")).pack(side=tk.LEFT)
    
    # Tercera fila de botones
    row3_frame = ttk.Frame(buttons_frame)
    row3_frame.pack(fill=tk.X)
    
    create_labeled_button(row3_frame, "🧪 Probar Captura", 
                         command=lambda: print("Probar captura")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row3_frame, "⚙️ Configuración", 
                         command=lambda: print("Configuración")).pack(side=tk.LEFT, padx=(0, 10))
    create_labeled_button(row3_frame, "👁️ Mostrar/Ocultar", 
                         command=lambda: print("Mostrar/Ocultar")).pack(side=tk.LEFT)
    
    # Frame para labels de estado
    status_frame = ttk.LabelFrame(main_frame, text="Estados del Sistema", padding="10")
    status_frame.pack(fill=tk.X, pady=(0, 10))
    
    # Estados
    status_grid = ttk.Frame(status_frame)
    status_grid.pack()
    
    states = [
        ("🟢 Sistema Funcionando", "green"),
        ("🟡 Advertencia", "orange"),
        ("🔴 Error", "red"),
        ("⚪ Desconocido", "gray"),
        ("💀 Fallo Total", "red"),
        ("✅ Operación Exitosa", "green")
    ]
    
    for i, (text, color) in enumerate(states):
        row = i // 2
        col = i % 2
        label = create_labeled_label(status_grid, text, foreground=color, 
                                   font=('Arial', 10, 'bold'))
        label.grid(row=row, column=col, sticky=tk.W, padx=(0, 20), pady=2)
    
    # Frame de información
    info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
    info_frame.pack(fill=tk.BOTH, expand=True)
    
    info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, font=('Consolas', 10))
    info_text.pack(fill=tk.BOTH, expand=True)
    
    info_content = """
Sistema de Iconos Implementado:

✅ Reemplazado emojis por iconos PNG en toda la aplicación
🎯 Iconos cargados desde assets/icons/
🖥️ Sistema de cache para mejorar rendimiento
⚙️ Fallback automático a emojis si los iconos no están disponibles
🔧 Funciones helper para crear botones y labels con iconos
📊 Compatibilidad total con la interfaz existente

Los iconos se cargan automáticamente cuando están disponibles,
y si no se encuentran, la aplicación usa los emojis originales
como respaldo.
    """
    
    info_text.insert(tk.END, info_content.strip())
    info_text.config(state=tk.DISABLED)
    
    # Información de debugging
    debug_frame = ttk.Frame(main_frame)
    debug_frame.pack(fill=tk.X, pady=(10, 0))
    
    # Verificar si los iconos están disponibles
    icons_path = icon_manager.icons_dir
    available = os.path.exists(icons_path)
    
    status_text = f"📁 Directorio de iconos: {icons_path}"
    status_color = "green" if available else "red"
    available_text = "✅ Disponible" if available else "❌ No encontrado"
    
    create_labeled_label(debug_frame, status_text, font=('Arial', 9)).pack(anchor=tk.W)
    create_labeled_label(debug_frame, available_text, foreground=status_color, 
                        font=('Arial', 9, 'bold')).pack(anchor=tk.W)
    
    root.mainloop()

if __name__ == "__main__":
    test_icon_system()
