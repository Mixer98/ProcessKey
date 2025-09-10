#!/usr/bin/env python3
"""
Administrador de Afinidad de Procesos
Software para gestionar la afinidad de CPU de procesos en Windows

Autor: Mixer98
Fecha: 9 de septiembre de 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import threading
import time
import os
import sys
import json
import keyboard
import uuid
import shutil
import winsound
from pynput import keyboard as pynput_keyboard
from typing import Dict, List, Optional, Any
import traceback
import pygame
import ctypes
import ctypes.wintypes
try:
    import numpy as np
except ImportError:
    np = None

from ui_components import UIComponents
from task_manager import TaskManager, TaskDialog

class AffinityManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Administrador de Afinidad de Procesos")
        
        # Maximizar la ventana al inicio
        self.root.state('zoomed')
        
        self.root.configure(bg='#f0f0f0')
        
        # Variables principales
        self.selected_process = None
        self.process_list = {}
        self.cpu_count = psutil.cpu_count()
        self.refresh_thread = None
        self.stop_refresh = False
        
        # Configuración de notificaciones
        self.notification_config = {
            'sound_enabled': True,
            'sound_file': None,
            'message_high': "🚀 Afinidad ALTA aplicada",
            'message_low': "💚 Afinidad BAJA aplicada",
            'show_process_name': True,
            'duration': 3000,
            'position': 'top-right'
        }
        self.config_file = "notification_config.json"
        
        # Verificar permisos de administrador
        self.is_admin = self.check_admin()
        
        # Inicializar componentes UI sin cargar tareas
        self.ui = UIComponents()
        self.ui.setup_ui(self)
        
        # Inicializar gestor de tareas
        self.task_manager = TaskManager(self)
        
        # Actualizar UI con las tareas cargadas
        self.ui.refresh_tasks_display(self)
        
        # Configurar interfaz
        self.refresh_process_list()
        self.load_notification_config()
        self.init_sound_system()
        
        # Configurar guardado automático
        self.setup_auto_save()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def check_admin(self) -> bool:
        """Verifica si la aplicación se ejecuta con permisos de administrador"""
        try:
            return os.getuid() == 0
        except AttributeError:
            # En Windows
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
    
    def log_message(self, message: str, level: str = "info"):
        """Agrega un mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        
        if level == "error":
            prefix = "❌"
        elif level == "warning":
            prefix = "⚠️"
        elif level == "success":
            prefix = "✅"
        else:
            prefix = "ℹ️"
        
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, f"[{timestamp}] {prefix} {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        else:
            # Si el widget de log aún no está disponible, imprimir en consola
            print(f"[{timestamp}] {prefix} {message}")
    
    def refresh_process_list(self):
        """Actualiza la lista de procesos"""
        self.log_message("Actualizando lista de procesos...")
        
        # Limpiar lista actual
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        self.process_list.clear()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    pinfo = proc.info
                    pid = pinfo['pid']
                    name = pinfo['name']
                    cpu_percent = pinfo['cpu_percent'] or 0
                    memory_mb = round(pinfo['memory_info'].rss / 1024 / 1024, 1) if pinfo['memory_info'] else 0
                    
                    # Agregar al treeview
                    item_id = self.process_tree.insert('', 'end', values=(
                        pid, name, f"{cpu_percent:.1f}%", f"{memory_mb:.1f}"
                    ))
                    
                    # Guardar referencia al proceso
                    self.process_list[item_id] = proc
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
            self.log_message(f"Lista actualizada: {len(self.process_list)} procesos encontrados", "success")
            
        except Exception as e:
            self.log_message(f"Error al actualizar procesos: {str(e)}", "error")
    
    def on_search_change(self, event=None):
        """Maneja los cambios en la barra de búsqueda"""
        search_text = self.search_var.get().lower()
        
        # Limpiar la vista actual
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Filtrar y mostrar procesos que coincidan
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                pinfo = proc.info
                pid = pinfo['pid']
                name = pinfo['name']
                
                # Filtrar por nombre o PID
                if (search_text in name.lower() or 
                    search_text in str(pid) or 
                    search_text == ""):
                    
                    cpu_percent = pinfo['cpu_percent'] or 0
                    memory_mb = round(pinfo['memory_info'].rss / 1024 / 1024, 1) if pinfo['memory_info'] else 0
                    
                    # Agregar al treeview
                    item_id = self.process_tree.insert('', 'end', values=(
                        pid, name, f"{cpu_percent:.1f}%", f"{memory_mb:.1f}"
                    ))
                    
                    # Guardar referencia al proceso
                    self.process_list[item_id] = proc
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    def clear_search(self):
        """Limpia la búsqueda y muestra todos los procesos"""
        self.search_var.set("")
        self.refresh_process_list()
    
    def on_process_select(self, event):
        """Maneja la selección de un proceso"""
        selection = self.process_tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        if item_id not in self.process_list:
            return
            
        self.selected_process = self.process_list[item_id]
        
        try:
            # Obtener información del proceso
            pid = self.selected_process.pid
            name = self.selected_process.name()
            
            # Obtener afinidad actual
            try:
                current_affinity = self.selected_process.cpu_affinity()
                affinity_str = ', '.join([f"CPU{cpu}" for cpu in current_affinity])
            except (psutil.AccessDenied, AttributeError):
                current_affinity = list(range(self.cpu_count))
                affinity_str = "Sin acceso (requiere permisos)"
            
            # Actualizar interfaz
            self.selected_process_label.config(text=name)
            self.pid_label.config(text=str(pid))
            self.current_affinity_label.config(text=affinity_str)
            
            # Actualizar checkboxes
            for i, var in enumerate(self.cpu_vars):
                var.set(i in current_affinity)
            
            self.apply_btn.config(state='normal')
            self.create_task_btn.config(state='normal')
            self.log_message(f"Proceso seleccionado: {name} (PID: {pid})")
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.log_message(f"Error al acceder al proceso: {str(e)}", "error")
            self.apply_btn.config(state='disabled')
            self.create_task_btn.config(state='disabled')
    
    def select_all_cpus(self):
        """Selecciona todas las CPUs"""
        for var in self.cpu_vars:
            var.set(True)
    
    def deselect_all_cpus(self):
        """Deselecciona todas las CPUs"""
        for var in self.cpu_vars:
            var.set(False)
    
    def apply_affinity(self):
        """Aplica la afinidad seleccionada al proceso"""
        if not self.selected_process:
            messagebox.showwarning("Advertencia", "No hay proceso seleccionado")
            return
        
        # Obtener CPUs seleccionadas
        selected_cpus = [i for i, var in enumerate(self.cpu_vars) if var.get()]
        
        if not selected_cpus:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos una CPU")
            return
        
        try:
            # Verificar que el proceso aún existe
            if not self.selected_process.is_running():
                messagebox.showerror("Error", "El proceso ya no está en ejecución")
                return
            
            # Aplicar nueva afinidad
            old_affinity = self.selected_process.cpu_affinity()
            self.selected_process.cpu_affinity(selected_cpus)
            
            # Verificar que se aplicó correctamente
            new_affinity = self.selected_process.cpu_affinity()
            
            if set(new_affinity) == set(selected_cpus):
                cpu_list = ', '.join([f"CPU{cpu}" for cpu in selected_cpus])
                self.log_message(
                    f"Afinidad aplicada exitosamente al proceso {self.selected_process.name()} "
                    f"(PID: {self.selected_process.pid}): {cpu_list}", 
                    "success"
                )
                
                # Actualizar la etiqueta de afinidad actual
                self.current_affinity_label.config(text=cpu_list)
                
                messagebox.showinfo("Éxito", 
                    f"Afinidad aplicada correctamente.\n"
                    f"Proceso: {self.selected_process.name()}\n"
                    f"CPUs: {cpu_list}")
            else:
                self.log_message(
                    f"Advertencia: La afinidad aplicada no coincide con la solicitada", 
                    "warning"
                )
                
        except psutil.AccessDenied:
            error_msg = (
                "Acceso denegado. Para modificar la afinidad de este proceso necesita:\n"
                "1. Ejecutar la aplicación como administrador\n"
                "2. O seleccionar un proceso de su propiedad"
            )
            messagebox.showerror("Error de Acceso", error_msg)
            self.log_message(
                f"Acceso denegado al modificar afinidad del proceso {self.selected_process.pid}", 
                "error"
            )
            
        except psutil.NoSuchProcess:
            messagebox.showerror("Error", "El proceso ya no existe")
            self.log_message("El proceso seleccionado ya no existe", "error")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.log_message(f"Error inesperado: {str(e)}", "error")
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            self.task_manager.save_automated_tasks()
            
            # Limpiar hotkeys
            for hotkey in list(self.task_manager.hotkey_listeners.keys()):
                self.task_manager.remove_hotkey_listener(hotkey)
            
            self.log_message("Aplicación cerrada correctamente", "info")
        except:
            pass
        
        self.root.destroy()
    
    def setup_auto_save(self):
        """Configura el guardado automático"""
        def auto_save():
            if not self.stop_refresh:
                self.task_manager.save_automated_tasks()
                self.root.after(300000, auto_save)  # 5 minutos
        
        self.root.after(300000, auto_save)
    
    def init_sound_system(self):
        """Inicializa el sistema de sonido"""
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)
        except Exception as e:
            self.log_message(f"Error inicializando sistema de sonido: {str(e)}", "warning")

    def load_notification_config(self):
        """Carga la configuración de notificaciones"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.notification_config.update(json.load(f))
        except Exception as e:
            self.log_message(f"Error cargando configuración: {str(e)}", "warning")

    def show_create_task_dialog(self):
        """Muestra el diálogo para crear una nueva tarea automatizada"""
        if not self.selected_process:
            messagebox.showwarning("Advertencia", "Primero seleccione un proceso en la pestaña 'Control Manual'")
            return
            
        # Recopilar información necesaria para la tarea
        task_data = {
            'name': f"Tarea para {self.selected_process.name()}",
            'process_name': self.selected_process.name(),
            'target_affinity': [i for i, var in enumerate(self.cpu_vars) if var.get()],
            'hotkey': ''
        }
        
        # Mostrar el diálogo para crear tarea
        dialog = TaskDialog(self.root, task_data)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # Agregar la tarea
            self.task_manager.add_task(dialog.result)
            
            # Actualizar la vista de tareas
            self.ui.refresh_tasks_display(self)
            
            # Cambiar a la pestaña de tareas
            self.notebook.select(1)  # El índice 1 corresponde a la pestaña de tareas

    def show_notification(self, message: str, mode: str = None):
        """Muestra una notificación en pantalla
        
        Args:
            message: El mensaje a mostrar
            mode: Modo de notificación (no usado actualmente, mantenido por compatibilidad)
        """
        try:
            # Crear una nueva ventana para la notificación
            notif = tk.Toplevel(self.root)
            notif.overrideredirect(True)
            notif.attributes('-topmost', True)
            
            # Configurar el estilo
            bg_color = "#4CAF50"  # Verde para todas las notificaciones
            icon = "🎯"  # Icono de objetivo para indicar que se aplicó la afinidad
            
            # Configurar la ventana
            notif.configure(bg=bg_color)
            
            # Frame principal con padding
            main_frame = ttk.Frame(notif, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Mensaje con icono
            msg_label = ttk.Label(main_frame, 
                                text=f"{icon} {message}",
                                font=('Arial', 10, 'bold'))
            msg_label.pack(pady=5)
            
            # Posicionar la ventana
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calcular dimensiones y posición
            notif.update_idletasks()
            width = notif.winfo_width() + 40
            height = notif.winfo_height() + 20
            
            # Posición basada en la configuración
            position = self.notification_config.get('position', 'top-right')
            if position == 'top-right':
                x = screen_width - width - 20
                y = 40
            elif position == 'top-left':
                x = 20
                y = 40
            elif position == 'bottom-right':
                x = screen_width - width - 20
                y = screen_height - height - 60
            else:  # bottom-left
                x = 20
                y = screen_height - height - 60
            
            # Aplicar posición
            notif.geometry(f"{width}x{height}+{x}+{y}")
            
            # Auto-cerrar después de un tiempo
            duration = self.notification_config.get('duration', 3000)
            notif.after(duration, notif.destroy)
            
        except Exception as e:
            self.log_message(f"Error mostrando notificación: {str(e)}", "error")

if __name__ == '__main__':
    root = tk.Tk()
    app = AffinityManager(root)
    root.mainloop()