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

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

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
        
        # Variables para la bandeja del sistema
        self.tray_icon = None
        self.is_minimized_to_tray = False
        self.tray_thread = None
        
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
        
        # Configurar event handler para minimizar (opcional)
        self.root.bind('<Unmap>', self.on_window_state_change)
        
        # Inicializar la pestaña de hotkeys
        self.initialize_hotkey_service_tab()

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
            # Detener el icono de la bandeja si existe
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    self.tray_icon.stop()
                except:
                    pass
            
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
    
    def clear_log(self):
        """Limpia el contenido del log"""
        try:
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.config(state='normal')
                self.log_text.delete(1.0, tk.END)
                self.log_text.config(state='disabled')
                self.log_message("Log limpiado", "info")
        except Exception as e:
            print(f"Error limpiando log: {str(e)}")
    
    def toggle_log_visibility(self):
        """Alterna la visibilidad del log"""
        try:
            if hasattr(self, 'log_visible') and hasattr(self, 'log_text') and hasattr(self, 'toggle_log_btn'):
                if self.log_visible.get():
                    # Ocultar log
                    self.log_text.grid_remove()
                    self.log_visible.set(False)
                    self.toggle_log_btn.config(text="👁️ Mostrar Log")
                else:
                    # Mostrar log
                    self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                    self.log_visible.set(True)
                    self.toggle_log_btn.config(text="👁️ Ocultar Log")
        except Exception as e:
            print(f"Error alternando visibilidad del log: {str(e)}")
    
    def create_tray_icon(self):
        """Crea el icono de la bandeja del sistema"""
        if not TRAY_AVAILABLE:
            self.log_message("Bandeja del sistema no disponible. Instale: pip install pystray pillow", "warning")
            return None
            
        try:
            # Crear una imagen simple para el icono
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            
            # Dibujar un icono simple (círculo con "A" para Afinidad)
            draw.ellipse([8, 8, 56, 56], fill='white', outline='black', width=2)
            draw.text((28, 22), "A", fill='black', anchor="mm")
            
            # Crear el menú contextual
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar", self.show_from_tray, default=True),
                pystray.MenuItem("Minimizar a bandeja", self.minimize_to_tray),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self.quit_app)
            )
            
            # Crear el icono de la bandeja
            icon = pystray.Icon("AffinityManager", image, "Administrador de Afinidad", menu)
            return icon
            
        except Exception as e:
            self.log_message(f"Error creando icono de bandeja: {str(e)}", "error")
            return None
    
    def minimize_to_tray(self, icon=None, item=None):
        """Minimiza la aplicación a la bandeja del sistema"""
        if not TRAY_AVAILABLE:
            self.log_message("Función de bandeja no disponible. Instale: pip install pystray pillow", "warning")
            return
            
        try:
            # Crear el icono de la bandeja si no existe
            if not self.tray_icon:
                self.tray_icon = self.create_tray_icon()
            
            if self.tray_icon:
                # Ocultar la ventana principal
                self.root.withdraw()
                self.is_minimized_to_tray = True
                
                # Ejecutar el icono de la bandeja en un hilo separado si no está ejecutándose
                if not self.tray_thread or not self.tray_thread.is_alive():
                    self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
                    self.tray_thread.start()
                
                self.log_message("Aplicación minimizada a la bandeja del sistema", "info")
            else:
                self.log_message("No se pudo crear el icono de la bandeja", "error")
        except Exception as e:
            self.log_message(f"Error minimizando a bandeja: {str(e)}", "error")
    
    def minimize_to_taskbar(self):
        """Alternativa simple: minimiza la ventana (sin usar bandeja del sistema)"""
        try:
            self.root.iconify()  # Minimizar la ventana normalmente
            self.log_message("Ventana minimizada", "info")
        except Exception as e:
            self.log_message(f"Error minimizando ventana: {str(e)}", "error")
    
    def smart_minimize(self):
        """Intenta minimizar a la bandeja, si no está disponible, minimiza normalmente"""
        if TRAY_AVAILABLE:
            self.minimize_to_tray()
        else:
            self.minimize_to_taskbar()
    
    def show_from_tray(self, icon=None, item=None):
        """Restaura la aplicación desde la bandeja del sistema"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_minimized_to_tray = False
            self.log_message("Aplicación restaurada desde la bandeja", "info")
        except Exception as e:
            self.log_message(f"Error restaurando desde bandeja: {str(e)}", "error")
    
    def quit_app(self, icon=None, item=None):
        """Cierra completamente la aplicación"""
        try:
            if self.tray_icon and self.tray_icon.visible:
                self.tray_icon.stop()
            self.on_closing()
        except Exception as e:
            self.log_message(f"Error cerrando aplicación: {str(e)}", "error")
    
    def on_window_state_change(self, event=None):
        """Maneja cambios en el estado de la ventana"""
        if event and str(event.type) == 'Unmap':
            # La ventana fue minimizada/ocultada
            if TRAY_AVAILABLE and not self.is_minimized_to_tray:
                # Opcional: minimizar automáticamente a la bandeja cuando se minimiza
                # self.minimize_to_tray()
                pass

    def restart_hotkey_service(self):
        """Reinicia el servicio de captura de hotkeys"""
        try:
            # Detener el servicio actual
            self.stop_hotkey_service()
            
            # Esperar un momento
            time.sleep(0.5)
            
            # Iniciar el servicio
            self.start_hotkey_service()
            
            self.log_message("Servicio de hotkeys reiniciado", "success")
            self.update_hotkey_service_status()
            
        except Exception as e:
            self.log_message(f"Error reiniciando servicio de hotkeys: {str(e)}", "error")
    
    def stop_hotkey_service(self):
        """Detiene el servicio de captura de hotkeys"""
        try:
            # Remover todos los listeners de hotkeys
            for hotkey in list(self.task_manager.hotkey_listeners.keys()):
                self.task_manager.remove_hotkey_listener(hotkey)
            
            # Actualizar estado en la UI
            if hasattr(self, 'service_status_label'):
                self.service_status_label.config(text="🔴 Detenido", foreground='red')
            
            self.log_message("Servicio de hotkeys detenido", "warning")
            self.update_hotkey_service_status()
            
        except Exception as e:
            self.log_message(f"Error deteniendo servicio de hotkeys: {str(e)}", "error")
    
    def start_hotkey_service(self):
        """Inicia el servicio de captura de hotkeys"""
        try:
            # Reconfigurar todos los hotkeys de las tareas
            for task_id, task in self.task_manager.automated_tasks.items():
                if task.get('hotkey'):
                    self.task_manager.setup_hotkey_listener(task['hotkey'], task_id)
            
            # Actualizar estado en la UI
            if hasattr(self, 'service_status_label'):
                self.service_status_label.config(text="🟢 Funcionando", foreground='green')
            
            self.log_message("Servicio de hotkeys iniciado", "success")
            self.update_hotkey_service_status()
            
        except Exception as e:
            self.log_message(f"Error iniciando servicio de hotkeys: {str(e)}", "error")
    
    def test_hotkey_capture(self):
        """Prueba la captura de hotkeys mostrando un diálogo de test"""
        try:
            # Crear ventana de prueba
            test_window = tk.Toplevel(self.root)
            test_window.title("🧪 Prueba de Captura de Hotkeys")
            test_window.geometry("500x300")
            test_window.transient(self.root)
            test_window.grab_set()
            
            # Centrar la ventana
            test_window.geometry("+%d+%d" % (
                self.root.winfo_rootx() + 100,
                self.root.winfo_rooty() + 100
            ))
            
            # Frame principal
            main_frame = ttk.Frame(test_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            ttk.Label(main_frame, text="Prueba de Captura de Teclas",
                     font=('Arial', 14, 'bold')).pack(pady=(0, 15))
            
            # Instrucciones
            instructions = ttk.Label(main_frame, 
                text="Presione cualquier combinación de teclas que desee probar.\n"
                     "El sistema detectará automáticamente la combinación.",
                font=('Arial', 10), justify=tk.CENTER)
            instructions.pack(pady=(0, 20))
            
            # Area de resultado
            result_frame = ttk.LabelFrame(main_frame, text="Resultado de la Captura", padding="10")
            result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Text widget para mostrar las capturas
            capture_text = tk.Text(result_frame, height=8, font=('Consolas', 10))
            capture_text.pack(fill=tk.BOTH, expand=True)
            capture_text.insert(tk.END, "Esperando captura de teclas...\n")
            
            # Variable para controlar el test
            test_active = [True]
            
            def on_key_event(e):
                if test_active[0]:
                    timestamp = time.strftime("%H:%M:%S")
                    key_info = f"[{timestamp}] Capturado: {e.name}\n"
                    capture_text.insert(tk.END, key_info)
                    capture_text.see(tk.END)
            
            # Configurar listener temporal
            test_hook = keyboard.on_press(on_key_event)
            
            def close_test():
                test_active[0] = False
                keyboard.unhook(test_hook)
                test_window.destroy()
            
            # Botón de cerrar
            ttk.Button(main_frame, text="Cerrar Prueba", 
                      command=close_test).pack(pady=(10, 0))
            
            # Manejar cierre de ventana
            test_window.protocol("WM_DELETE_WINDOW", close_test)
            
            self.log_message("Iniciada prueba de captura de hotkeys", "info")
            
        except Exception as e:
            self.log_message(f"Error en prueba de captura: {str(e)}", "error")
    
    def update_hotkey_service_status(self):
        """Actualiza el estado del servicio de hotkeys en la UI"""
        try:
            if hasattr(self, 'active_hotkeys_label'):
                # Contar hotkeys activos
                active_count = len(self.task_manager.hotkey_listeners)
                self.active_hotkeys_label.config(text=str(active_count))
            
            if hasattr(self, 'hotkeys_tree'):
                # Actualizar la lista de hotkeys
                self.refresh_hotkeys_display()
                
        except Exception as e:
            self.log_message(f"Error actualizando estado del servicio: {str(e)}", "error")
    
    def refresh_hotkeys_display(self):
        """Actualiza la visualización de hotkeys en el treeview"""
        try:
            if not hasattr(self, 'hotkeys_tree'):
                return
                
            # Limpiar treeview
            for item in self.hotkeys_tree.get_children():
                self.hotkeys_tree.delete(item)
            
            # Agregar hotkeys activos
            for hotkey, task_id in self.task_manager.hotkey_listeners.items():
                if task_id in self.task_manager.automated_tasks:
                    task_data = self.task_manager.automated_tasks[task_id]
                    
                    # Obtener estadísticas del hotkey (si existen)
                    stats = getattr(self.task_manager, 'hotkey_stats', {}).get(hotkey, {})
                    last_used = stats.get('last_used', 'Nunca')
                    usage_count = stats.get('count', 0)
                    
                    # Estado del hotkey
                    status = "🟢 Activo" if hotkey in self.task_manager.hotkey_listeners else "🔴 Inactivo"
                    
                    self.hotkeys_tree.insert('', 'end', values=(
                        hotkey,
                        task_data.get('name', 'Sin nombre'),
                        task_data.get('process_name', 'Sin proceso'),
                        status,
                        last_used,
                        usage_count
                    ))
                    
        except Exception as e:
            self.log_message(f"Error actualizando visualización de hotkeys: {str(e)}", "error")
    
    def save_hotkey_config(self):
        """Guarda la configuración del servicio de hotkeys"""
        try:
            config = {
                'capture_delay': self.capture_delay_var.get() if hasattr(self, 'capture_delay_var') else "100",
                'debug_mode': self.debug_mode_var.get() if hasattr(self, 'debug_mode_var') else False,
                'service_enabled': True
            }
            
            with open('hotkey_service_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.log_message("Configuración de hotkeys guardada", "success")
            
        except Exception as e:
            self.log_message(f"Error guardando configuración de hotkeys: {str(e)}", "error")
    
    def load_hotkey_config(self):
        """Carga la configuración del servicio de hotkeys"""
        try:
            if os.path.exists('hotkey_service_config.json'):
                with open('hotkey_service_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Aplicar configuración
                if hasattr(self, 'capture_delay_var'):
                    self.capture_delay_var.set(config.get('capture_delay', '100'))
                if hasattr(self, 'debug_mode_var'):
                    self.debug_mode_var.set(config.get('debug_mode', False))
                
                self.log_message("Configuración de hotkeys cargada", "success")
            else:
                self.log_message("No se encontró archivo de configuración de hotkeys", "warning")
                
        except Exception as e:
            self.log_message(f"Error cargando configuración de hotkeys: {str(e)}", "error")
    
    def reset_hotkey_config(self):
        """Restaura la configuración por defecto del servicio de hotkeys"""
        try:
            if hasattr(self, 'capture_delay_var'):
                self.capture_delay_var.set("100")
            if hasattr(self, 'debug_mode_var'):
                self.debug_mode_var.set(False)
            
            self.log_message("Configuración de hotkeys restaurada por defecto", "success")
            
        except Exception as e:
            self.log_message(f"Error restaurando configuración por defecto: {str(e)}", "error")

    def initialize_hotkey_service_tab(self):
        """Inicializa la pestaña de servicio de hotkeys con valores por defecto"""
        try:
            # Cargar configuración guardada
            self.load_hotkey_config()
            
            # Actualizar estado del servicio
            self.update_hotkey_service_status()
            
            # Configurar actualización periódica del estado
            def update_service_status():
                try:
                    self.update_hotkey_service_status()
                    if hasattr(self, 'capture_errors_label'):
                        # Aquí podrías agregar lógica para contar errores reales
                        self.capture_errors_label.config(text="0")
                except:
                    pass
                # Programar próxima actualización en 5 segundos
                self.root.after(5000, update_service_status)
            
            # Iniciar actualizaciones automáticas
            self.root.after(1000, update_service_status)
            
            self.log_message("Pestaña de servicio de hotkeys inicializada", "success")
            
        except Exception as e:
            self.log_message(f"Error inicializando pestaña de hotkeys: {str(e)}", "error")

if __name__ == '__main__':
    root = tk.Tk()
    app = AffinityManager(root)
    root.mainloop()