#!/usr/bin/env python3
"""
Administrador de Afinidad de Procesos
Software para gestionar la afinidad de CPU de procesos en Windows

Autor: Usuario
Fecha: 9 de septiembre de 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
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

class AffinityManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Administrador de Afinidad de Procesos")
        
        # Maximizar la ventana al inicio
        self.root.state('zoomed')  # En Windows maximiza la ventana
        
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.selected_process = None
        self.process_list = {}
        self.cpu_count = psutil.cpu_count()
        self.refresh_thread = None
        self.stop_refresh = False
        
        # Variables para tareas automatizadas
        self.automated_tasks = {}  # {task_id: task_info}
        self.hotkey_listeners = {}  # {hotkey: task_id}
        self.tasks_file = "automated_tasks.json"
        self.keyboard_thread = None
        self.current_recording = None
        
        # Variables para notificaciones
        self.notification_config = {
            'sound_enabled': True,
            'sound_file': None,  # None = sonido del sistema
            'message_high': "🚀 Afinidad ALTA aplicada",
            'message_low': "💚 Afinidad BAJA aplicada",
            'show_process_name': True,
            'duration': 3000,  # milliseconds
            'position': 'top-right'  # top-right, top-left, center
        }
        self.config_file = "notification_config.json"
        
        # Verificar permisos de administrador
        self.is_admin = self.check_admin()
        
        self.setup_ui()
        self.refresh_process_list()
        self.load_automated_tasks()
        self.load_notification_config()
        self.init_sound_system()
        self.setup_keyboard_monitoring()
        
        # Configurar guardado automático cada 5 minutos
        self.setup_auto_save()
        
        # Configurar cierre de aplicación
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
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar peso de las filas y columnas para mejor proporcionalidad
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3, minsize=800)  # Notebook ocupa 75% del espacio
        main_frame.columnconfigure(1, weight=1, minsize=350)  # Log ocupa 25% del espacio
        main_frame.rowconfigure(0, weight=0)  # Fila del título sin peso
        main_frame.rowconfigure(1, weight=1)  # Fila principal con todo el peso
        
        # Título más destacado
        title_label = ttk.Label(main_frame, text="🖥️ Administrador de Afinidad de Procesos", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # Advertencia de permisos (solo si no es admin)
        if not self.is_admin:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.grid(row=0, column=0, columnspan=2, pady=(35, 15), sticky=(tk.W, tk.E))
            
            warning_label = ttk.Label(warning_frame, 
                                    text="⚠️ Ejecute como administrador para modificar la afinidad de todos los procesos",
                                    foreground='red', font=('Arial', 10, 'bold'))
            warning_label.pack()
        
        # Crear notebook para pestañas (lado izquierdo - 75% del espacio)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))

        # Frame derecho - Registro de Actividad (25% del espacio)
        log_frame = ttk.LabelFrame(main_frame, text="📝 Registro de Actividad", padding="8")
        log_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # Log de actividad más grande y mejor proporcionado
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, state='disabled', 
                                                 width=45, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Pestaña 1: Control Manual
        manual_frame = ttk.Frame(self.notebook)
        self.notebook.add(manual_frame, text="🎯 Control Manual")
        
        # Configurar grid para pestaña manual con mejor proporcionalidad
        manual_frame.columnconfigure(0, weight=2, minsize=500)  # Lista de procesos - 60%
        manual_frame.columnconfigure(1, weight=1, minsize=350)  # Control afinidad - 40%
        manual_frame.rowconfigure(0, weight=1)
        
        # Frame izquierdo - Lista de procesos (60% del espacio)
        left_frame = ttk.LabelFrame(manual_frame, text="📋 Procesos en Ejecución", padding="8")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # Frame superior para controles de procesos
        process_controls_frame = ttk.Frame(left_frame)
        process_controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        process_controls_frame.columnconfigure(0, weight=1)
        
        # Barra de búsqueda
        search_frame = ttk.Frame(process_controls_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Button(search_frame, text="Limpiar", command=self.clear_search).grid(row=0, column=2)
        
        # Botón de actualizar
        refresh_btn = ttk.Button(process_controls_frame, text="Actualizar Lista", 
                                command=self.refresh_process_list)
        refresh_btn.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Treeview para mostrar procesos - mejor dimensionado para ventana maximizada
        columns = ('PID', 'Nombre', 'CPU%', 'Memoria')
        self.process_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=25)
        
        # Configurar columnas con mejor proporción
        self.process_tree.heading('PID', text='PID')
        self.process_tree.heading('Nombre', text='Nombre del Proceso')
        self.process_tree.heading('CPU%', text='CPU %')
        self.process_tree.heading('Memoria', text='Memoria (MB)')
        
        # Anchos mejorados para ventana maximizada
        self.process_tree.column('PID', width=90, minwidth=70)
        self.process_tree.column('Nombre', width=300, minwidth=200)
        self.process_tree.column('CPU%', width=90, minwidth=70)
        self.process_tree.column('Memoria', width=120, minwidth=90)
        
        self.process_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para el treeview
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind evento de selección
        self.process_tree.bind('<<TreeviewSelect>>', self.on_process_select)
        
        # Frame derecho - Control de afinidad (40% del espacio)
        right_frame = ttk.LabelFrame(manual_frame, text="⚙️ Control de Afinidad de CPU", padding="8")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(2, weight=1)
        right_frame.columnconfigure(0, weight=1)
        
        # Información del proceso seleccionado - más espaciada
        info_frame = ttk.LabelFrame(right_frame, text="📊 Información del Proceso", padding="8")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Proceso Seleccionado:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.selected_process_label = ttk.Label(info_frame, text="Ninguno", font=('Arial', 10, 'bold'), foreground='blue')
        self.selected_process_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        ttk.Label(info_frame, text="PID:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.pid_label = ttk.Label(info_frame, text="-", font=('Arial', 10))
        self.pid_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        ttk.Label(info_frame, text="Afinidad Actual:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.current_affinity_label = ttk.Label(info_frame, text="-", font=('Arial', 10))
        self.current_affinity_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Frame para seleccionar CPUs - más espacioso
        cpu_frame = ttk.LabelFrame(right_frame, text=f"🔧 Seleccionar CPUs ({self.cpu_count} disponibles)", padding="10")
        cpu_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Checkboxes para cada CPU - mejor organizados
        self.cpu_vars = []
        self.cpu_checkboxes = []
        
        # Crear checkboxes en una cuadrícula más espaciada
        cols = min(6, max(2, self.cpu_count // 2))  # Mejor distribución basada en cantidad de CPUs
        for i in range(self.cpu_count):
            var = tk.BooleanVar()
            self.cpu_vars.append(var)
            
            checkbox = ttk.Checkbutton(cpu_frame, text=f"CPU {i}", variable=var)
            row = i // cols
            col = i % cols
            checkbox.grid(row=row, column=col, sticky=tk.W, padx=8, pady=5)
            self.cpu_checkboxes.append(checkbox)
        
        # Botones de control de CPUs - mejor organizados
        cpu_button_frame = ttk.Frame(right_frame)
        cpu_button_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        cpu_button_frame.columnconfigure(0, weight=1)
        cpu_button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(cpu_button_frame, text="✅ Seleccionar Todas", 
                  command=self.select_all_cpus).grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(cpu_button_frame, text="❌ Deseleccionar Todas", 
                  command=self.deselect_all_cpus).grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Botones principales - más destacados
        self.apply_btn = ttk.Button(right_frame, text="🚀 Aplicar Afinidad", 
                                   command=self.apply_affinity, state='disabled',
                                   style='Accent.TButton')
        self.apply_btn.grid(row=4, column=0, pady=(15, 8), sticky=(tk.W, tk.E))
        
        self.create_task_btn = ttk.Button(right_frame, text="🔧 Crear Tarea Automatizada", 
                                         command=self.show_create_task_dialog, state='disabled')
        self.create_task_btn.grid(row=5, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Pestaña 2: Tareas Automatizadas
        self.setup_automated_tasks_tab()
        
        # Pestaña 3: Configuración de Notificaciones
        self.setup_notifications_tab()
        
        # Configurar peso de filas para redimensionamiento
        main_frame.rowconfigure(1, weight=1)  # Área principal
        
        self.log_message("Aplicación iniciada correctamente")
        if not self.is_admin:
            self.log_message("ADVERTENCIA: Ejecute como administrador para acceso completo", "warning")
    
    def log_message(self, message: str, level: str = "info"):
        """Agrega un mensaje al log"""
        timestamp = time.strftime("%H:%M:%S")
        
        self.log_text.config(state='normal')
        
        if level == "error":
            prefix = "❌"
        elif level == "warning":
            prefix = "⚠️"
        elif level == "success":
            prefix = "✅"
        else:
            prefix = "ℹ️"
            
        self.log_text.insert(tk.END, f"[{timestamp}] {prefix} {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
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
            # Guardar tareas antes de cerrar
            self.save_automated_tasks()
            
            # Limpiar hotkeys
            for hotkey in list(self.hotkey_listeners.keys()):
                self.remove_hotkey_listener(hotkey)
            
            self.log_message("Aplicación cerrada correctamente", "info")
        except:
            pass
        
        self.root.destroy()
    
    def setup_automated_tasks_tab(self):
        """Configura la pestaña de tareas automatizadas"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="⚡ Tareas Automatizadas")
        
        tasks_frame.columnconfigure(0, weight=1)
        tasks_frame.rowconfigure(1, weight=1)
        
        # Frame superior - Controles mejorados
        control_frame = ttk.LabelFrame(tasks_frame, text="🎛️ Controles de Tareas", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Primera fila de botones
        buttons_frame1 = ttk.Frame(control_frame)
        buttons_frame1.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(buttons_frame1, text="➕ Nueva Tarea", 
                  command=self.show_create_task_dialog).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame1, text="✏️ Editar Tarea", 
                  command=self.edit_selected_task).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame1, text="🗑️ Eliminar Tarea", 
                  command=self.delete_selected_task).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame1, text="🧪 Probar Tarea", 
                  command=self.test_selected_task).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame1, text="🔍 Diagnóstico", 
                  command=self.diagnose_tasks_system).pack(side=tk.LEFT)
        
        # Estado del monitoreo de teclado - más destacado
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=1, column=0, pady=8, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="🔘 Estado del Sistema:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.keyboard_status_label = ttk.Label(status_frame, text="Iniciando...", 
                                              foreground='orange', font=('Arial', 9, 'bold'))
        self.keyboard_status_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # Información sobre hotkeys globales - más visible
        info_label = ttk.Label(control_frame, 
                              text="💡 Los hotkeys funcionan globalmente (incluso en pantalla completa)", 
                              font=('Arial', 9, 'bold'), foreground='blue')
        info_label.grid(row=2, column=0, pady=(5, 0))
        
        # Frame central - Lista de tareas mejorada
        list_frame = ttk.LabelFrame(tasks_frame, text="📋 Tareas Configuradas", padding="8")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview para mostrar tareas - optimizado para ventana maximizada
        task_columns = ('Nombre', 'Proceso', 'Hotkey', 'Afinidad Alta', 'Afinidad Baja', 'Tipo Alerta', 'Estado')
        self.tasks_tree = ttk.Treeview(list_frame, columns=task_columns, show='headings', height=20)
        
        # Configurar columnas de tareas con mejor proporción
        self.tasks_tree.heading('Nombre', text='📝 Nombre de la Tarea')
        self.tasks_tree.heading('Proceso', text='🎯 Proceso Objetivo')
        self.tasks_tree.heading('Hotkey', text='⌨️ Combinación de Teclas')
        self.tasks_tree.heading('Afinidad Alta', text='⬆️ Afinidad Alta')
        self.tasks_tree.heading('Afinidad Baja', text='⬇️ Afinidad Baja')
        self.tasks_tree.heading('Tipo Alerta', text='🔔 Tipo de Alerta')
        self.tasks_tree.heading('Estado', text='📊 Estado')
        
        # Anchos optimizados para ventana maximizada
        self.tasks_tree.column('Nombre', width=180, minwidth=120)
        self.tasks_tree.column('Proceso', width=140, minwidth=100)
        self.tasks_tree.column('Hotkey', width=140, minwidth=100)
        self.tasks_tree.column('Afinidad Alta', width=120, minwidth=80)
        self.tasks_tree.column('Afinidad Baja', width=120, minwidth=80)
        self.tasks_tree.column('Tipo Alerta', width=110, minwidth=80)
        self.tasks_tree.column('Estado', width=60)
        
        self.tasks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para el treeview de tareas
        tasks_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        tasks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tasks_tree.configure(yscrollcommand=tasks_scrollbar.set)
        
        # Cargar tareas existentes en el treeview
        self.refresh_tasks_display()
    
    def refresh_tasks_display(self):
        """Actualiza la visualización de tareas en el treeview"""
        # Limpiar treeview
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Agregar tareas cargadas
        for task_id, task_data in self.automated_tasks.items():
            high_affinity_str = ', '.join([f"CPU{cpu}" for cpu in task_data['high_affinity']])
            low_affinity_str = ', '.join([f"CPU{cpu}" for cpu in task_data['low_affinity']])
            alert_type = task_data.get('alert_type', 'combinado').capitalize()
            
            self.tasks_tree.insert('', 'end', iid=task_id, values=(
                task_data['name'],
                task_data['process_name'],
                task_data['hotkey'],
                high_affinity_str,
                low_affinity_str,
                alert_type,
                "Activa"
            ))
    
    def show_create_task_dialog(self):
        """Muestra el diálogo para crear una nueva tarea automatizada"""
        if not self.selected_process:
            messagebox.showwarning("Advertencia", "Primero seleccione un proceso en la pestaña 'Control Manual'")
            return
        
        dialog = TaskDialog(self.root, self, self.selected_process)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.add_automated_task(dialog.result)
    
    def edit_selected_task(self):
        """Edita la tarea seleccionada"""
        try:
            selection = self.tasks_tree.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Seleccione una tarea para editar")
                return
            
            task_id = selection[0]
            if task_id not in self.automated_tasks:
                messagebox.showerror("Error", "Tarea no encontrada")
                return
            
            task_data = self.automated_tasks[task_id].copy()  # Hacer copia para evitar problemas
            dialog = TaskDialog(self.root, self, None, task_data)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                # Eliminar la tarea anterior correctamente
                old_hotkey = task_data.get('hotkey')
                if old_hotkey:
                    self.remove_hotkey_listener(old_hotkey)
                
                # Eliminar del treeview y diccionario
                self.tasks_tree.delete(task_id)
                del self.automated_tasks[task_id]
                
                # Agregar la tarea modificada
                self.add_automated_task(dialog.result)
                
                self.log_message(f"Tarea editada correctamente: {dialog.result['name']}", "success")
                
        except Exception as e:
            self.log_message(f"Error editando tarea: {str(e)}", "error")
            messagebox.showerror("Error", f"No se pudo editar la tarea: {str(e)}")
    
    def delete_selected_task(self):
        """Elimina la tarea seleccionada"""
        try:
            selection = self.tasks_tree.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Seleccione una tarea para eliminar")
                return
            
            task_id = selection[0]
            if task_id not in self.automated_tasks:
                messagebox.showerror("Error", "Tarea no encontrada")
                return
            
            task_data = self.automated_tasks[task_id].copy()  # Hacer copia
            
            # Confirmar eliminación
            if messagebox.askyesno("Confirmar", f"¿Eliminar la tarea '{task_data['name']}'?"):
                try:
                    # Remover listener de hotkey correctamente
                    hotkey = task_data.get('hotkey')
                    if hotkey and hotkey in self.hotkey_listeners:
                        self.remove_hotkey_listener(hotkey)
                    
                    # Eliminar del treeview primero
                    self.tasks_tree.delete(task_id)
                    
                    # Eliminar de la estructura de datos
                    del self.automated_tasks[task_id]
                    
                    # Guardar cambios
                    self.save_automated_tasks()
                    
                    self.log_message(f"Tarea eliminada correctamente: {task_data['name']}", "success")
                    
                    # Limpiar selección para evitar problemas
                    self.tasks_tree.selection_remove(self.tasks_tree.selection())
                    
                except Exception as e:
                    self.log_message(f"Error eliminando tarea: {str(e)}", "error")
                    messagebox.showerror("Error", f"No se pudo eliminar la tarea: {str(e)}")
                    # Recargar la vista en caso de error
                    self.refresh_tasks_display()
        
        except Exception as e:
            self.log_message(f"Error en delete_selected_task: {str(e)}", "error")
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            self.refresh_tasks_display()
    
    def test_selected_task(self):
        """Prueba la tarea seleccionada"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una tarea para probar")
            return
        
        task_id = selection[0]
        if task_id in self.automated_tasks:
            self.execute_automated_task(task_id)
    
    def add_automated_task(self, task_data):
        """Agrega una nueva tarea automatizada"""
        import uuid
        task_id = str(uuid.uuid4())
        
        # Agregar a la estructura de datos
        self.automated_tasks[task_id] = task_data
        
        # Agregar al treeview
        high_affinity_str = ', '.join([f"CPU{cpu}" for cpu in task_data['high_affinity']])
        low_affinity_str = ', '.join([f"CPU{cpu}" for cpu in task_data['low_affinity']])
        alert_type = task_data.get('alert_type', 'combinado').capitalize()
        
        self.tasks_tree.insert('', 'end', iid=task_id, values=(
            task_data['name'],
            task_data['process_name'],
            task_data['hotkey'],
            high_affinity_str,
            low_affinity_str,
            alert_type,
            "Activa"
        ))
        
        # Configurar el hotkey
        self.setup_hotkey_listener(task_data['hotkey'], task_id)
        
        # Guardar cambios
        self.save_automated_tasks()
        self.log_message(f"Tarea automatizada creada: {task_data['name']} - Hotkey: {task_data['hotkey']}", "success")
    
    def setup_hotkey_listener(self, hotkey, task_id):
        """Configura un listener GLOBAL para una combinación de teclas"""
        try:
            # Remover listener anterior si existe
            if hotkey in self.hotkey_listeners:
                self.remove_hotkey_listener(hotkey)
            
            # Crear callback thread-safe
            def callback():
                # Ejecutar en el hilo principal para evitar problemas de threading
                self.root.after(0, lambda: self.execute_automated_task(task_id))
            
            # Configurar hotkey global (funciona en pantalla completa)
            keyboard.add_hotkey(hotkey, callback, suppress=False, trigger_on_release=False)
            self.hotkey_listeners[hotkey] = task_id
            
            self.log_message(f"Hotkey global configurado: {hotkey} (funciona en pantalla completa)", "success")
            
        except Exception as e:
            self.log_message(f"Error configurando hotkey {hotkey}: {str(e)}", "error")
    
    def remove_hotkey_listener(self, hotkey):
        """Remueve un listener de hotkey"""
        try:
            if hotkey in self.hotkey_listeners:
                keyboard.remove_hotkey(hotkey)
                del self.hotkey_listeners[hotkey]
        except Exception as e:
            self.log_message(f"Error removiendo hotkey {hotkey}: {str(e)}", "error")
    
    def execute_automated_task(self, task_id):
        """Ejecuta una tarea automatizada"""
        if task_id not in self.automated_tasks:
            return
        
        task_data = self.automated_tasks[task_id]
        
        try:
            # Buscar el proceso por nombre
            target_process = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == task_data['process_name'].lower():
                    target_process = proc
                    break
            
            if not target_process:
                self.log_message(f"Proceso no encontrado: {task_data['process_name']}", "warning")
                return
            
            # Obtener afinidad actual
            current_affinity = target_process.cpu_affinity()
            
            # Determinar nueva afinidad (alternar entre alta y baja)
            if set(current_affinity) == set(task_data['high_affinity']):
                new_affinity = task_data['low_affinity']
                mode = "Baja"
            else:
                new_affinity = task_data['high_affinity']
                mode = "Alta"
            
            # Aplicar nueva afinidad
            target_process.cpu_affinity(new_affinity)
            
            # Actualizar estado en el treeview
            affinity_str = ', '.join([f"CPU{cpu}" for cpu in new_affinity])
            
            self.log_message(
                f"Tarea ejecutada: {task_data['name']} - {task_data['process_name']} "
                f"→ Afinidad {mode}: {affinity_str}", 
                "success"
            )
            
            # Guardar nombre del proceso para notificación
            self._last_process_name = task_data['process_name']
            
            # Mostrar notificación con configuración personalizada si existe
            notification_mode = "high" if mode == "Alta" else "low"
            self.show_notification_for_task(task_data, notification_mode)
            
        except psutil.AccessDenied:
            self.log_message(
                f"Acceso denegado al ejecutar tarea: {task_data['name']}", 
                "error"
            )
        except Exception as e:
            self.log_message(
                f"Error ejecutando tarea {task_data['name']}: {str(e)}", 
                "error"
            )
    
    def show_notification(self, message, mode="info"):
        """Muestra una notificación mejorada que funciona sobre Minecraft y juegos"""
        try:
            # Reproducir sonido si está habilitado
            if self.notification_config['sound_enabled']:
                self.play_notification_sound()
            
            # Crear notificación ultra-visible
            self.create_game_overlay_notification(message, mode)
            
        except Exception as e:
            # Fallback: solo log si la notificación falla
            self.log_message(f"Notificación: {message}", "info")
    
    def show_notification_for_task(self, task_data, mode="info"):
        """Muestra notificación usando configuración personalizada de la tarea o global"""
        try:
            # Obtener tipo de alerta
            alert_type = task_data.get('alert_type', 'combinado')
            
            # Usar configuración personalizada si existe
            custom_config = task_data.get('custom_notification')
            if custom_config:
                # Guardar configuración original temporalmente
                original_config = self.notification_config.copy()
                
                # Aplicar configuración personalizada
                self.notification_config.update(custom_config)
                
                try:
                    # Ejecutar según tipo de alerta
                    if alert_type in ['sound', 'combinado']:
                        if custom_config['sound_enabled']:
                            self.play_notification_sound_custom(custom_config)
                    
                    if alert_type in ['overlay', 'combinado']:
                        self.create_game_overlay_notification("", mode)
                    
                    # El log siempre se ejecuta (ya se hizo en execute_automated_task)
                    
                finally:
                    # Restaurar configuración original
                    self.notification_config = original_config
            else:
                # Usar configuración global según tipo de alerta
                if alert_type in ['sound', 'combinado']:
                    if self.notification_config['sound_enabled']:
                        self.play_notification_sound()
                
                if alert_type in ['overlay', 'combinado']:
                    self.create_game_overlay_notification("", mode)
                
                # El log ya se ejecutó en execute_automated_task
                
        except Exception as e:
            self.log_message(f"Error en notificación personalizada: {str(e)}", "error")
            # Fallback a notificación simple
            self.log_message(f"Tarea ejecutada: {task_data['name']}", "info")
    
    def play_notification_sound_custom(self, custom_config):
        """Reproduce sonido usando configuración personalizada"""
        try:
            if not self.sound_initialized:
                return
                
            sound_file = custom_config.get('sound_file')
            
            if sound_file and os.path.exists(sound_file):
                # Reproducir archivo personalizado específico de la tarea
                try:
                    sound = pygame.mixer.Sound(sound_file)
                    sound.play()
                except Exception as e:
                    self.log_message(f"Error reproduciendo sonido personalizado de tarea: {str(e)}", "warning")
                    self.play_system_sound()
            else:
                # Usar sonido del sistema
                self.play_system_sound()
                
        except Exception as e:
            self.log_message(f"Error reproduciendo sonido personalizado: {str(e)}", "warning")
    
    def create_game_overlay_notification(self, message, mode="info"):
        """Crea una notificación que se ve sobre juegos en pantalla completa"""
        try:
            # Crear ventana especial para overlay
            notification = tk.Toplevel()
            notification.title("Afinidad Manager")
            
            # Configuraciones críticas para aparecer sobre juegos SIN robar foco
            notification.wm_attributes('-topmost', True)
            notification.wm_attributes('-alpha', 0.95)
            notification.overrideredirect(True)  # Sin bordes de ventana
            
            # NO usar focus_force() ni SetForegroundWindow() para evitar salir de pantalla completa
            notification.lift()
            
            # Forzar que aparezca sobre TODO pero SIN robar foco
            hwnd = notification.winfo_id()
            try:
                # Usar SetWindowPos con SWP_NOACTIVATE para no robar foco
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002  
                SWP_NOACTIVATE = 0x0010
                SWP_SHOWWINDOW = 0x0040
                HWND_TOPMOST = -1
                
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
            except Exception as e:
                self.log_message(f"Advertencia: No se pudo forzar overlay: {e}", "warning")
            
            # Determinar mensaje personalizado
            if mode == "high":
                display_message = self.notification_config['message_high']
                bg_color = '#27AE60'  # Verde
                icon = "🚀"
            elif mode == "low":
                display_message = self.notification_config['message_low'] 
                bg_color = '#3498DB'  # Azul
                icon = "💚"
            else:
                display_message = message
                bg_color = '#2C3E50'  # Gris oscuro
                icon = "🎯"
            
            # Agregar nombre del proceso si está configurado
            if self.notification_config['show_process_name'] and hasattr(self, '_last_process_name'):
                display_message += f"\n{self._last_process_name}"
            
            # Cálculo mejorado del tamaño dinámico basado en contenido
            lines = display_message.split('\n')
            max_line_length = max([len(line) for line in lines]) if lines else 20
            num_lines = len(lines)
            
            # Tamaño más preciso basado en caracteres y líneas
            char_width = 9  # Aproximadamente 9 pixels por carácter en Arial 10
            line_height = 22  # Altura de línea en pixels
            
            width = max(350, min(800, max_line_length * char_width + 80))  # Min 350, Max 800
            height = max(100, 80 + num_lines * line_height)  # Altura base + líneas
            
            notification.geometry(f"{width}x{height}")
            
            # Posicionamiento según configuración
            self.position_notification(notification)
            
            # Estilo visual impactante
            main_frame = tk.Frame(notification, bg=bg_color, padx=20, pady=15,
                                relief='raised', bd=3)
            main_frame.pack(fill='both', expand=True)
            
            # Título con ícono
            title_label = tk.Label(main_frame, text=f"{icon} Afinidad Manager", 
                                 font=('Arial', 12, 'bold'), 
                                 fg='white', bg=bg_color)
            title_label.pack()
            
            # Mensaje principal con mejor ajuste de texto
            msg_label = tk.Label(main_frame, text=display_message, 
                               font=('Arial', 11, 'bold'), 
                               fg='white', bg=bg_color,
                               wraplength=width-60,  # Más margen para el texto
                               justify='center',
                               padx=10, pady=5)
            msg_label.pack(pady=(8, 0), expand=True)
            
            # Animación de entrada
            notification.attributes('-alpha', 0)
            self.fade_in_notification(notification)
            
            # Auto-cerrar después del tiempo configurado
            notification.after(self.notification_config['duration'], 
                             lambda: self.fade_out_notification(notification))
            
        except Exception as e:
            # Fallback más simple
            self.simple_notification_fallback(message)

    def fade_out_notification(self, notification):
        """Animación de salida para la notificación"""
        try:
            alpha = notification.attributes('-alpha')
            if alpha > 0:
                notification.attributes('-alpha', alpha - 0.05)
                notification.after(30, lambda: self.fade_out_notification(notification))
            else:
                notification.destroy()
        except:
            try:
                notification.destroy()
            except:
                pass

    def simple_notification_fallback(self, message):
        """Notificación de respaldo si falla la principal"""
        try:
            messagebox.showinfo("Afinidad Manager", message)
        except:
            print(f"Notificación: {message}")

    def init_sound_system(self):
        """Inicializa el sistema de sonido"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_initialized = True
            self.log_message("Sistema de sonido inicializado correctamente", "success")
        except Exception as e:
            self.sound_initialized = False
            self.log_message(f"Error inicializando sonido: {str(e)}", "warning")

    def play_notification_sound(self):
        """Reproduce sonido de notificación"""
        try:
            if not self.sound_initialized:
                return
                
            sound_file = self.notification_config.get('sound_file')
            
            if sound_file and os.path.exists(sound_file):
                # Reproducir archivo de sonido personalizado
                try:
                    sound = pygame.mixer.Sound(sound_file)
                    sound.play()
                except Exception as e:
                    self.log_message(f"Error reproduciendo sonido personalizado: {str(e)}", "warning")
                    self.play_system_sound()
            else:
                # Reproducir sonido del sistema
                self.play_system_sound()
                
        except Exception as e:
            self.log_message(f"Error reproduciendo sonido: {str(e)}", "warning")

    def play_system_sound(self):
        """Reproduce sonido del sistema de Windows"""
        try:
            # Usar API de Windows para sonido del sistema
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                return
            except ImportError:
                # winsound solo está disponible en Windows
                pass
        except Exception:
            pass
        
        # Fallback: sonido generado (solo si numpy está disponible)
        try:
            if np is not None and self.sound_initialized:
                # Generar un beep simple con pygame
                duration = 200  # milisegundos
                frequency = 800  # Hz
                
                sample_rate = 22050
                frames = int(duration * sample_rate / 1000)
                
                arr = []
                for i in range(frames):
                    wave = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate)
                    arr.append([int(wave), int(wave)])
                
                sound = pygame.sndarray.make_sound(np.array(arr))
                sound.play()
        except:
            pass

    def setup_notifications_tab(self):
        """Configura la pestaña de configuración de notificaciones"""
        notif_frame = ttk.Frame(self.notebook)
        self.notebook.add(notif_frame, text="🔔 Configuración de Notificaciones")
        
        notif_frame.columnconfigure(0, weight=1)
        notif_frame.rowconfigure(0, weight=1)
        
        # Crear canvas para scroll
        canvas = tk.Canvas(notif_frame)
        scrollbar = ttk.Scrollbar(notif_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Contenido principal
        main_frame = ttk.LabelFrame(scrollable_frame, text="Configuración de Notificaciones", padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sección: Sonido
        sound_frame = ttk.LabelFrame(main_frame, text="Configuración de Sonido", padding="10")
        sound_frame.pack(fill=tk.X, pady=(0, 15))
        sound_frame.columnconfigure(1, weight=1)
        
        # Habilitar sonido
        self.sound_enabled_var = tk.BooleanVar(value=self.notification_config['sound_enabled'])
        ttk.Checkbutton(sound_frame, text="Habilitar sonido en notificaciones", 
                       variable=self.sound_enabled_var,
                       command=self.on_sound_config_change).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Archivo de sonido
        ttk.Label(sound_frame, text="Archivo de sonido personalizado:").grid(row=1, column=0, sticky=tk.W)
        self.sound_file_var = tk.StringVar(value=self.notification_config.get('sound_file', ''))
        self.sound_file_entry = ttk.Entry(sound_frame, textvariable=self.sound_file_var, width=40)
        self.sound_file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        ttk.Button(sound_frame, text="Seleccionar", 
                  command=self.select_sound_file).grid(row=1, column=2, padx=(5, 0))
        
        # Botones de sonido
        sound_btn_frame = ttk.Frame(sound_frame)
        sound_btn_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        ttk.Button(sound_btn_frame, text="Probar Sonido Personalizado", 
                  command=self.test_custom_sound).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(sound_btn_frame, text="Probar Sonido del Sistema", 
                  command=self.test_system_sound).pack(side=tk.LEFT)
        
        # Sección: Mensajes
        msg_frame = ttk.LabelFrame(main_frame, text="Configuración de Mensajes", padding="10")
        msg_frame.pack(fill=tk.X, pady=(0, 15))
        msg_frame.columnconfigure(1, weight=1)
        
        # Mensaje para afinidad alta
        ttk.Label(msg_frame, text="Mensaje para afinidad ALTA:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.msg_high_var = tk.StringVar(value=self.notification_config['message_high'])
        ttk.Entry(msg_frame, textvariable=self.msg_high_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        
        # Mensaje para afinidad baja
        ttk.Label(msg_frame, text="Mensaje para afinidad BAJA:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.msg_low_var = tk.StringVar(value=self.notification_config['message_low'])
        ttk.Entry(msg_frame, textvariable=self.msg_low_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        
        # Mostrar nombre del proceso
        self.show_process_var = tk.BooleanVar(value=self.notification_config['show_process_name'])
        ttk.Checkbutton(msg_frame, text="Mostrar nombre del proceso en la notificación", 
                       variable=self.show_process_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Sección: Visualización
        visual_frame = ttk.LabelFrame(main_frame, text="Configuración Visual", padding="10")
        visual_frame.pack(fill=tk.X, pady=(0, 15))
        visual_frame.columnconfigure(1, weight=1)
        
        # Duración
        ttk.Label(visual_frame, text="Duración (milisegundos):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.duration_var = tk.IntVar(value=self.notification_config['duration'])
        duration_spinbox = ttk.Spinbox(visual_frame, from_=1000, to=10000, increment=500, 
                                      textvariable=self.duration_var, width=10)
        duration_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))
        
        # Posición
        ttk.Label(visual_frame, text="Posición en pantalla:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.position_var = tk.StringVar(value=self.notification_config['position'])
        position_combo = ttk.Combobox(visual_frame, textvariable=self.position_var, 
                                     values=['top-right', 'top-left', 'center'], 
                                     state='readonly', width=15)
        position_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))
        
        # Sección: Pruebas
        test_frame = ttk.LabelFrame(main_frame, text="Probar Notificaciones", padding="10")
        test_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botones de prueba
        test_btn_frame = ttk.Frame(test_frame)
        test_btn_frame.pack(fill=tk.X)
        
        ttk.Button(test_btn_frame, text="Probar Notificación ALTA", 
                  command=lambda: self.test_notification("high")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(test_btn_frame, text="Probar Notificación BAJA", 
                  command=lambda: self.test_notification("low")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(test_btn_frame, text="Probar Overlay sobre Juego", 
                  command=self.test_game_overlay).pack(side=tk.LEFT)
        
        # Botones de control
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(control_frame, text="Guardar Configuración", 
                  command=self.save_notification_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Restablecer Valores por Defecto", 
                  command=self.reset_notification_config).pack(side=tk.LEFT)
        
    def select_sound_file(self):
        """Selecciona un archivo de sonido personalizado"""
        filetypes = [
            ("Archivos de sonido", "*.wav *.mp3 *.ogg"),
            ("WAV", "*.wav"),
            ("MP3", "*.mp3"),
            ("OGG", "*.ogg"),
            ("Todos los archivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de sonido",
            filetypes=filetypes
        )
        
        if filename:
            self.sound_file_var.set(filename)
            self.log_message(f"Archivo de sonido seleccionado: {os.path.basename(filename)}", "info")
    
    def test_custom_sound(self):
        """Prueba el sonido personalizado"""
        sound_file = self.sound_file_var.get()
        if sound_file and os.path.exists(sound_file):
            try:
                if not self.sound_initialized:
                    self.init_sound_system()
                
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                self.log_message("Reproduciendo sonido personalizado...", "info")
            except Exception as e:
                messagebox.showerror("Error", f"Error reproduciendo sonido: {str(e)}")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un archivo de sonido válido primero")
    
    def test_system_sound(self):
        """Prueba el sonido del sistema"""
        try:
            self.play_system_sound()
            self.log_message("Reproduciendo sonido del sistema...", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Error reproduciendo sonido del sistema: {str(e)}")
    
    def test_notification(self, mode):
        """Prueba las notificaciones"""
        self._last_process_name = "Proceso de Prueba"
        self.show_notification("", mode)
    
    def test_game_overlay(self):
        """Prueba la notificación overlay específicamente para juegos"""
        self._last_process_name = "Minecraft.exe"
        
        # Crear un overlay de prueba ultra-visible
        self.create_game_overlay_notification("🎮 PRUEBA DE OVERLAY SOBRE JUEGO\nEsta notificación debería verse sobre Minecraft", "info")
        
        self.log_message("Prueba de overlay ejecutada. ¿Se ve sobre juegos en pantalla completa?", "info")
    
    def on_sound_config_change(self):
        """Maneja cambios en la configuración de sonido"""
        self.notification_config['sound_enabled'] = self.sound_enabled_var.get()
    
    def save_notification_config(self):
        """Guarda la configuración de notificaciones"""
        try:
            # Actualizar configuración con valores de la interfaz
            self.notification_config.update({
                'sound_enabled': self.sound_enabled_var.get(),
                'sound_file': self.sound_file_var.get() if self.sound_file_var.get() else None,
                'message_high': self.msg_high_var.get(),
                'message_low': self.msg_low_var.get(),
                'show_process_name': self.show_process_var.get(),
                'duration': self.duration_var.get(),
                'position': self.position_var.get()
            })
            
            # Guardar en archivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.notification_config, f, indent=2, ensure_ascii=False)
            
            self.log_message("Configuración de notificaciones guardada correctamente", "success")
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            
        except Exception as e:
            self.log_message(f"Error guardando configuración: {str(e)}", "error")
            messagebox.showerror("Error", f"Error guardando configuración: {str(e)}")
    
    def load_notification_config(self):
        """Carga la configuración de notificaciones desde archivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                self.notification_config.update(saved_config)
                self.log_message("Configuración de notificaciones cargada", "success")
        except Exception as e:
            self.log_message(f"Error cargando configuración de notificaciones: {str(e)}", "warning")
    
    def reset_notification_config(self):
        """Restablece la configuración de notificaciones a valores por defecto"""
        if messagebox.askyesno("Confirmar", "¿Restablecer configuración a valores por defecto?"):
            # Valores por defecto
            default_config = {
                'sound_enabled': True,
                'sound_file': None,
                'message_high': "🚀 Afinidad ALTA aplicada",
                'message_low': "💚 Afinidad BAJA aplicada",
                'show_process_name': True,
                'duration': 3000,
                'position': 'top-right'
            }
            
            self.notification_config = default_config
            
            # Actualizar interfaz
            self.sound_enabled_var.set(default_config['sound_enabled'])
            self.sound_file_var.set('')
            self.msg_high_var.set(default_config['message_high'])
            self.msg_low_var.set(default_config['message_low'])
            self.show_process_var.set(default_config['show_process_name'])
            self.duration_var.set(default_config['duration'])
            self.position_var.set(default_config['position'])
            
            self.log_message("Configuración restablecida a valores por defecto", "success")
    
    def position_notification(self, notification):
        """Posiciona la notificación según la configuración"""
        notification.update_idletasks()
        
        screen_width = notification.winfo_screenwidth()
        screen_height = notification.winfo_screenheight()
        width = notification.winfo_width()
        height = notification.winfo_height()
        
        position = self.notification_config['position']
        
        if position == 'top-right':
            x = screen_width - width - 20
            y = 20
        elif position == 'top-left':
            x = 20
            y = 20
        elif position == 'center':
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        else:  # default top-right
            x = screen_width - width - 20
            y = 20
            
        notification.geometry(f"+{x}+{y}")
    
    def fade_in_notification(self, notification):
        """Animación de entrada para la notificación"""
        try:
            alpha = notification.attributes('-alpha')
            if alpha < 0.95:
                notification.attributes('-alpha', alpha + 0.05)
                notification.after(20, lambda: self.fade_in_notification(notification))
        except:
            pass
    
    def fade_out_notification(self, notification):
        """Animación de salida para la notificación"""
        try:
            alpha = notification.attributes('-alpha')
            if alpha > 0.1:
                notification.attributes('-alpha', alpha - 0.05)
                notification.after(30, lambda: self.fade_out_notification(notification))
            else:
                notification.destroy()
        except:
            try:
                notification.destroy()
            except:
                pass
    
    def simple_notification_fallback(self, message):
        """Notificación simple en caso de error con la avanzada"""
        try:
            # Crear ventana simple pero efectiva
            notification = tk.Toplevel()
            notification.title("Afinidad")
            notification.geometry("250x80")
            notification.attributes('-topmost', True)
            
            tk.Label(notification, text=message, 
                    font=('Arial', 9), wraplength=200).pack(pady=20)
            
            notification.after(2000, notification.destroy)
        except:
            # Último recurso: beep del sistema
            try:
                ctypes.windll.user32.MessageBeep(0x40)  # MB_ICONASTERISK
            except:
                pass
    
    def setup_keyboard_monitoring(self):
        """Configura el monitoreo de teclado global mejorado"""
        def keyboard_worker():
            try:
                # Actualizar estado en la interfaz usando after() para thread-safety
                self.root.after(0, lambda: self.keyboard_status_label.config(
                    text="Estado: ✅ Activo (Global)", foreground='green'))
                
                # Inicializar monitoreo global
                self.log_message("Monitoreo de hotkeys globales iniciado (funciona en pantalla completa)", "success")
                
                # Mantener el thread activo para escuchar eventos
                while True:
                    time.sleep(0.1)  # Pequeña pausa para no sobrecargar el CPU
                    
            except Exception as e:
                error_msg = f"Error en monitoreo de teclado: {str(e)}"
                self.root.after(0, lambda: self.log_message(error_msg, "error"))
                self.root.after(0, lambda: self.keyboard_status_label.config(
                    text="Estado: ❌ Error", foreground='red'))
        
        self.keyboard_thread = threading.Thread(target=keyboard_worker, daemon=True)
        self.keyboard_thread.start()
    
    def load_automated_tasks(self):
        """Carga las tareas automatizadas desde archivo"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                
                loaded_count = 0
                error_count = 0
                
                for task_id, task_data in tasks_data.items():
                    # Validar datos de la tarea
                    if self.validate_task_data(task_data):
                        self.automated_tasks[task_id] = task_data
                        
                        # Configurar hotkey
                        try:
                            self.setup_hotkey_listener(task_data['hotkey'], task_id)
                            loaded_count += 1
                        except Exception as e:
                            self.log_message(f"Error configurando hotkey para {task_data['name']}: {str(e)}", "warning")
                            error_count += 1
                    else:
                        self.log_message(f"Tarea inválida ignorada: {task_data.get('name', 'Sin nombre')}", "warning")
                        error_count += 1
                
                if loaded_count > 0:
                    self.log_message(f"✅ Cargadas {loaded_count} tareas automatizadas", "success")
                    
                    # Actualizar visualización si existe el treeview
                    if hasattr(self, 'tasks_tree'):
                        self.refresh_tasks_display()
                    
                    # Guardar cambios si se hicieron correcciones automáticas
                    self.save_automated_tasks()
                    
                if error_count > 0:
                    self.log_message(f"⚠️ {error_count} tareas tuvieron errores", "warning")
                    
            else:
                self.log_message("No se encontró archivo de tareas previo. Iniciando con tareas vacías.", "info")
                
        except Exception as e:
            self.log_message(f"Error cargando tareas: {str(e)}", "error")
    
    def validate_task_data(self, task_data):
        """Valida y corrige los datos de una tarea"""
        try:
            required_fields = ['name', 'process_name', 'hotkey', 'high_affinity', 'low_affinity']
            
            # Verificar campos requeridos
            for field in required_fields:
                if field not in task_data:
                    self.log_message(f"Tarea inválida: falta campo '{field}'", "warning")
                    return False
            
            # Agregar campos opcionales con valores por defecto si no existen
            if 'alert_type' not in task_data:
                task_data['alert_type'] = 'combinado'  # Valor por defecto
                self.log_message("Campo 'alert_type' agregado automáticamente", "info")
            
            if 'custom_notification' not in task_data:
                task_data['custom_notification'] = None  # Sin notificación personalizada por defecto
                
            # Validar que las afinidades sean listas válidas
            if (not isinstance(task_data['high_affinity'], list) or 
                not isinstance(task_data['low_affinity'], list)):
                self.log_message("Afinidades deben ser listas válidas", "warning")
                return False
                
            # Validar que las CPUs estén en rango válido
            max_cpu = self.cpu_count - 1
            for cpu in task_data['high_affinity'] + task_data['low_affinity']:
                if not isinstance(cpu, int) or cpu < 0 or cpu > max_cpu:
                    self.log_message(f"CPU {cpu} fuera de rango válido (0-{max_cpu})", "warning")
                    return False
                    
            return True
            
        except Exception as e:
            self.log_message(f"Error validando tarea: {str(e)}", "error")
            return False
    
    def save_automated_tasks(self):
        """Guarda las tareas automatizadas en archivo con respaldo"""
        try:
            # Crear respaldo si existe archivo anterior
            if os.path.exists(self.tasks_file):
                backup_file = self.tasks_file + '.backup'
                import shutil
                shutil.copy2(self.tasks_file, backup_file)
            
            # Guardar datos actuales
            temp_file = self.tasks_file + '.temp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.automated_tasks, f, indent=2, ensure_ascii=False)
            
            # Reemplazar archivo original solo si el temporal se escribió correctamente
            import shutil
            shutil.move(temp_file, self.tasks_file)
            
            self.log_message(f"✅ Tareas guardadas: {len(self.automated_tasks)} configuraciones", "success")
            
        except Exception as e:
            self.log_message(f"❌ Error guardando tareas: {str(e)}", "error")
            # Intentar restaurar desde backup si existe
            backup_file = self.tasks_file + '.backup'
            if os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.copy2(backup_file, self.tasks_file)
                    self.log_message("Archivo restaurado desde respaldo", "warning")
                except:
                    pass
    
    def setup_auto_save(self):
        """Configura el guardado automático periódico"""
        def auto_save():
            if self.automated_tasks:  # Solo guardar si hay tareas
                self.save_automated_tasks()
            # Programar el siguiente guardado en 5 minutos (300000 ms)
            self.root.after(300000, auto_save)
        
        # Iniciar el primer guardado automático en 5 minutos
        self.root.after(300000, auto_save)
        self.log_message("Guardado automático configurado (cada 5 minutos)", "info")
    
    def diagnose_tasks_system(self):
        """Diagnóstica el sistema de tareas para detectar problemas"""
        try:
            self.log_message("🔍 Iniciando diagnóstico del sistema de tareas...", "info")
            
            # Verificar archivo de tareas
            if os.path.exists(self.tasks_file):
                file_size = os.path.getsize(self.tasks_file)
                self.log_message(f"📁 Archivo de tareas encontrado: {self.tasks_file} ({file_size} bytes)", "info")
            else:
                self.log_message(f"❌ Archivo de tareas no encontrado: {self.tasks_file}", "warning")
            
            # Verificar tareas en memoria
            task_count = len(self.automated_tasks)
            self.log_message(f"📊 Tareas en memoria: {task_count}", "info")
            
            # Verificar hotkeys registrados
            hotkey_count = len(self.hotkey_listeners)
            self.log_message(f"⌨️ Hotkeys registrados: {hotkey_count}", "info")
            
            # Verificar cada tarea
            for task_id, task_data in self.automated_tasks.items():
                name = task_data.get('name', 'Sin nombre')
                hotkey = task_data.get('hotkey', 'Sin hotkey')
                alert_type = task_data.get('alert_type', 'No definido')
                
                self.log_message(f"  📋 Tarea: {name} | Hotkey: {hotkey} | Tipo: {alert_type}", "info")
                
                # Verificar si el hotkey está registrado
                if hotkey in self.hotkey_listeners:
                    self.log_message(f"    ✅ Hotkey registrado correctamente", "success")
                else:
                    self.log_message(f"    ❌ Hotkey NO registrado", "error")
                    # Intentar registrar nuevamente
                    try:
                        self.setup_hotkey_listener(hotkey, task_id)
                        self.log_message(f"    🔧 Hotkey re-registrado automáticamente", "success")
                    except Exception as e:
                        self.log_message(f"    ❌ Error re-registrando hotkey: {str(e)}", "error")
            
            # Verificar treeview
            if hasattr(self, 'tasks_tree'):
                treeview_items = len(self.tasks_tree.get_children())
                self.log_message(f"🌳 Items en TreeView: {treeview_items}", "info")
                
                if treeview_items != task_count:
                    self.log_message(f"⚠️ Desincronización detectada. Actualizando TreeView...", "warning")
                    self.refresh_tasks_display()
                    self.log_message(f"✅ TreeView actualizado", "success")
            
            self.log_message("🏁 Diagnóstico completado", "success")
            
        except Exception as e:
            self.log_message(f"❌ Error en diagnóstico: {str(e)}", "error")


class TaskDialog:
    """Diálogo para crear/editar tareas automatizadas"""
    
    def __init__(self, parent, manager, process=None, task_data=None):
        self.parent = parent
        self.manager = manager
        self.process = process
        self.result = None
        self.recording_hotkey = False
        
        # Crear ventana de diálogo (tamaño optimizado con scroll)
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configurar Tarea Automatizada")
        self.dialog.geometry("700x600")  # Ancho mayor, alto menor (scroll compensa)
        self.dialog.minsize(650, 400)    # Tamaño mínimo
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar la ventana
        self.center_dialog()
        
        self.setup_dialog_ui(task_data)
    
    def center_dialog(self):
        """Centra el diálogo en la pantalla"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_dialog_ui(self, task_data=None):
        """Configura la interfaz del diálogo con scroll"""
        # Crear canvas y scrollbar para scroll
        canvas = tk.Canvas(self.dialog, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        
        # Frame principal que contendrá todo el contenido
        main_frame = ttk.Frame(canvas, padding="20")
        
        # Configurar el scroll y redimensionamiento
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_canvas_width(event):
            # Ajustar ancho del contenido al ancho del canvas
            canvas_width = event.width
            canvas.itemconfig(canvas_window_id, width=canvas_width-4)  # -4 para márgenes
        
        main_frame.bind("<Configure>", configure_scroll_region)
        
        canvas_window_id = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.bind('<Configure>', configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind del scroll del mouse y teclado
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_key_scroll(event):
            if event.keysym == 'Up':
                canvas.yview_scroll(-3, "units")
            elif event.keysym == 'Down':
                canvas.yview_scroll(3, "units")
            elif event.keysym == 'Page_Up':
                canvas.yview_scroll(-10, "units")
            elif event.keysym == 'Page_Down':
                canvas.yview_scroll(10, "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.dialog.bind('<Key>', _on_key_scroll)
        
        # Hacer que la ventana sea focusable para recibir eventos de teclado
        self.dialog.focus_set()
        
        # Guardar referencia al canvas para limpieza
        self.canvas = canvas
        
        # Al cerrar la ventana, limpiar el bind del mouse
        self.dialog.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
        
        # Título con indicador de scroll
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_text = "Editar Tarea" if task_data else "Nueva Tarea Automatizada"
        ttk.Label(title_frame, text=title_text, font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Indicador de scroll
        scroll_hint = ttk.Label(title_frame, text="💡 Usa scroll o rueda del mouse para ver más opciones", 
                               font=('Arial', 8), foreground='gray')
        scroll_hint.pack(side=tk.RIGHT)
        
        # Nombre de la tarea
        ttk.Label(main_frame, text="Nombre de la tarea:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=50).pack(fill=tk.X, pady=(5, 15))
        
        # Proceso objetivo
        ttk.Label(main_frame, text="Proceso objetivo:").pack(anchor=tk.W)
        self.process_var = tk.StringVar()
        process_frame = ttk.Frame(main_frame)
        process_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Entry(process_frame, textvariable=self.process_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(process_frame, text="Detectar", command=self.detect_process).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Combinación de teclas
        ttk.Label(main_frame, text="Combinación de teclas:").pack(anchor=tk.W)
        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.pack(fill=tk.X, pady=(5, 15))
        
        self.hotkey_var = tk.StringVar()
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.hotkey_var, width=30)
        self.hotkey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.record_btn = ttk.Button(hotkey_frame, text="Grabar", command=self.record_hotkey)
        self.record_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Instrucciones para hotkeys
        instructions = ttk.Label(main_frame, 
            text="Ejemplos: ctrl+alt+h, ctrl+shift+g, f1, ctrl+f1\n"
                 "Use 'Grabar' para capturar la combinación automáticamente",
            font=('Arial', 8), foreground='gray')
        instructions.pack(pady=(0, 15))
        
        # Afinidad Alta (Rendimiento)
        ttk.Label(main_frame, text="Afinidad ALTA (Rendimiento máximo):").pack(anchor=tk.W)
        self.high_cpu_frame = ttk.Frame(main_frame)
        self.high_cpu_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.high_cpu_vars = []
        cols = 4
        for i in range(self.manager.cpu_count):
            var = tk.BooleanVar()
            self.high_cpu_vars.append(var)
            
            checkbox = ttk.Checkbutton(self.high_cpu_frame, text=f"CPU {i}", variable=var)
            row = i // cols
            col = i % cols
            checkbox.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
        
        # Botones para afinidad alta
        high_btn_frame = ttk.Frame(main_frame)
        high_btn_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Button(high_btn_frame, text="Todas", command=self.select_all_high).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(high_btn_frame, text="Ninguna", command=self.deselect_all_high).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(high_btn_frame, text="Última Mitad", command=self.select_last_half_high).pack(side=tk.LEFT)
        
        # Afinidad Baja (Ahorro de energía)
        ttk.Label(main_frame, text="Afinidad BAJA (Ahorro de energía):").pack(anchor=tk.W)
        self.low_cpu_frame = ttk.Frame(main_frame)
        self.low_cpu_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.low_cpu_vars = []
        for i in range(self.manager.cpu_count):
            var = tk.BooleanVar()
            self.low_cpu_vars.append(var)
            
            checkbox = ttk.Checkbutton(self.low_cpu_frame, text=f"CPU {i}", variable=var)
            row = i // cols
            col = i % cols
            checkbox.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
        
        # Botones para afinidad baja
        low_btn_frame = ttk.Frame(main_frame)
        low_btn_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Button(low_btn_frame, text="Todas", command=self.select_all_low).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(low_btn_frame, text="Ninguna", command=self.deselect_all_low).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(low_btn_frame, text="Primera Mitad", command=self.select_first_half_low).pack(side=tk.LEFT)
        
        # Tipos de alerta disponibles
        alert_types_label = ttk.Label(main_frame, text="Tipos de Alerta Disponibles", font=('Arial', 12, 'bold'))
        alert_types_label.pack(anchor=tk.W, pady=(15, 10))
        
        alert_info_frame = ttk.LabelFrame(main_frame, text="Información de Tipos", padding="10")
        alert_info_frame.pack(fill=tk.X, pady=(0, 15))
        
        alert_info_text = tk.Text(alert_info_frame, height=4, wrap=tk.WORD, state='disabled',
                                 font=('Arial', 9), bg='#f8f9fa', relief='flat')
        alert_info_text.pack(fill=tk.X)
        
        alert_info_text.config(state='normal')
        alert_info_text.insert(tk.END, "📊 Overlay Visual: Notificación semi-transparente que aparece sobre cualquier aplicación\n")
        alert_info_text.insert(tk.END, "🔊 Sonido: Reproduce sonido personalizado o del sistema\n") 
        alert_info_text.insert(tk.END, "📝 Log: Registra la acción en el registro de actividad\n")
        alert_info_text.insert(tk.END, "🎯 Combinado: Overlay + Sonido + Log (recomendado para gaming)")
        alert_info_text.config(state='disabled')
        
        # Selector de tipo de alerta
        alert_type_frame = ttk.Frame(main_frame)
        alert_type_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(alert_type_frame, text="Tipo de alerta:").pack(anchor=tk.W, pady=(0, 5))
        
        self.alert_type = tk.StringVar(value="combinado")
        alert_types = [
            ("Overlay Visual", "overlay"),
            ("Solo Sonido", "sound"),
            ("Solo Log", "log"),
            ("Combinado (Recomendado)", "combinado")
        ]
        
        for text, value in alert_types:
            ttk.Radiobutton(alert_type_frame, text=text, variable=self.alert_type, 
                           value=value).pack(anchor=tk.W, padx=20)

        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(15, 15))
        
        # Configuración de Notificaciones Personalizadas
        notif_label = ttk.Label(main_frame, text="Configuración de Notificaciones", font=('Arial', 12, 'bold'))
        notif_label.pack(anchor=tk.W, pady=(15, 10))
        
        # Usar configuración global o personalizada
        self.use_custom_notification = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Usar configuración personalizada para esta tarea", 
                       variable=self.use_custom_notification, 
                       command=self.toggle_notification_config).pack(anchor=tk.W, pady=(0, 10))
        
        # Frame para configuración personalizada (inicialmente oculto)
        self.custom_notif_frame = ttk.LabelFrame(main_frame, text="Configuración Personalizada", padding="10")
        
        # Sonido personalizado
        sound_frame = ttk.Frame(self.custom_notif_frame)
        sound_frame.pack(fill=tk.X, pady=(0, 10))
        sound_frame.columnconfigure(1, weight=1)
        
        self.custom_sound_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(sound_frame, text="Habilitar sonido", variable=self.custom_sound_enabled).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(sound_frame, text="Archivo de sonido:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.custom_sound_file = tk.StringVar()
        ttk.Entry(sound_frame, textvariable=self.custom_sound_file, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=(5, 0))
        ttk.Button(sound_frame, text="...", width=3, command=self.select_custom_sound).grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        
        # Mensajes personalizados
        msg_frame = ttk.Frame(self.custom_notif_frame)
        msg_frame.pack(fill=tk.X, pady=(10, 10))
        msg_frame.columnconfigure(1, weight=1)
        
        ttk.Label(msg_frame, text="Mensaje afinidad ALTA:").grid(row=0, column=0, sticky=tk.W)
        self.custom_msg_high = tk.StringVar(value="🚀 Afinidad ALTA aplicada")
        ttk.Entry(msg_frame, textvariable=self.custom_msg_high, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        
        ttk.Label(msg_frame, text="Mensaje afinidad BAJA:").grid(row=1, column=0, sticky=tk.W)
        self.custom_msg_low = tk.StringVar(value="💚 Afinidad BAJA aplicada")
        ttk.Entry(msg_frame, textvariable=self.custom_msg_low, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0))
        
        # Configuración visual
        visual_frame = ttk.Frame(self.custom_notif_frame)
        visual_frame.pack(fill=tk.X, pady=(10, 10))
        visual_frame.columnconfigure(1, weight=1)
        
        ttk.Label(visual_frame, text="Duración (ms):").grid(row=0, column=0, sticky=tk.W)
        self.custom_duration = tk.IntVar(value=3000)
        ttk.Spinbox(visual_frame, from_=1000, to=10000, increment=500, 
                   textvariable=self.custom_duration, width=8).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(visual_frame, text="Posición:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.custom_position = tk.StringVar(value="top-right")
        pos_combo = ttk.Combobox(visual_frame, textvariable=self.custom_position, 
                                values=['top-right', 'top-left', 'center'], 
                                state='readonly', width=12)
        pos_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        self.custom_show_process = tk.BooleanVar(value=True)
        ttk.Checkbutton(visual_frame, text="Mostrar nombre del proceso", 
                       variable=self.custom_show_process).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Botón de prueba
        ttk.Button(self.custom_notif_frame, text="Probar Notificación Personalizada", 
                  command=self.test_custom_notification).pack(pady=(10, 0))
        
        # Separador final para espacio antes de botones fijos
        ttk.Frame(main_frame).pack(pady=20)  # Espacio final en el scroll
        
        # Actualizar canvas cuando cambie el contenido
        main_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Botones fijos en la parte inferior (fuera del scroll)
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Cancelar", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Aceptar", command=self.accept).pack(side=tk.RIGHT)
        
        # Cargar datos si es edición
        if task_data:
            self.load_task_data(task_data)
        else:
            # Valores por defecto para nueva tarea
            if self.process:
                self.process_var.set(self.process.name())
                self.name_var.set(f"Tarea para {self.process.name()}")
            
            # Afinidad alta por defecto (todas las CPUs)
            for var in self.high_cpu_vars:
                var.set(True)
            
            # Afinidad baja por defecto (solo CPU 0)
            if self.low_cpu_vars:
                self.low_cpu_vars[0].set(True)
    
    def detect_process(self):
        """Detecta el proceso seleccionado actualmente"""
        if self.process:
            self.process_var.set(self.process.name())
        else:
            messagebox.showinfo("Información", "Seleccione un proceso en la pestaña 'Control Manual' primero")
    
    def record_hotkey(self):
        """Graba una combinación de teclas"""
        if self.recording_hotkey:
            return
        
        self.recording_hotkey = True
        self.record_btn.config(text="Presione teclas...", state='disabled')
        self.hotkey_entry.config(state='disabled')
        
        def on_key_combination(event):
            # Construir string de hotkey
            keys = []
            if event.state & 0x4:  # Control
                keys.append('ctrl')
            if event.state & 0x1:  # Shift
                keys.append('shift')
            if event.state & 0x8:  # Alt
                keys.append('alt')
            
            # Agregar la tecla principal
            key = event.keysym.lower()
            if key not in ['control_l', 'control_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r']:
                keys.append(key)
                
                hotkey_string = '+'.join(keys)
                self.hotkey_var.set(hotkey_string)
                
                # Restaurar estado
                self.recording_hotkey = False
                self.record_btn.config(text="Grabar", state='normal')
                self.hotkey_entry.config(state='normal')
                self.dialog.unbind('<KeyPress>')
        
        self.dialog.bind('<KeyPress>', on_key_combination)
        self.dialog.focus_set()
    
    def select_all_high(self):
        """Selecciona todas las CPUs para afinidad alta"""
        for var in self.high_cpu_vars:
            var.set(True)
    
    def deselect_all_high(self):
        """Deselecciona todas las CPUs para afinidad alta"""
        for var in self.high_cpu_vars:
            var.set(False)
    
    def select_last_half_high(self):
        """Selecciona la última mitad de CPUs para afinidad alta"""
        half = len(self.high_cpu_vars) // 2
        for i, var in enumerate(self.high_cpu_vars):
            var.set(i >= half)
    
    def select_all_low(self):
        """Selecciona todas las CPUs para afinidad baja"""
        for var in self.low_cpu_vars:
            var.set(True)
    
    def deselect_all_low(self):
        """Deselecciona todas las CPUs para afinidad baja"""
        for var in self.low_cpu_vars:
            var.set(False)
    
    def select_first_half_low(self):
        """Selecciona la primera mitad de CPUs para afinidad baja"""
        half = len(self.low_cpu_vars) // 2
        for i, var in enumerate(self.low_cpu_vars):
            var.set(i < half)
    
    def load_task_data(self, task_data):
        """Carga datos de una tarea existente"""
        self.name_var.set(task_data['name'])
        self.process_var.set(task_data['process_name'])
        self.hotkey_var.set(task_data['hotkey'])
        
        # Cargar afinidad alta
        for i, var in enumerate(self.high_cpu_vars):
            var.set(i in task_data['high_affinity'])
        
        # Cargar afinidad baja
        for i, var in enumerate(self.low_cpu_vars):
            var.set(i in task_data['low_affinity'])
        
        # Cargar tipo de alerta
        self.alert_type.set(task_data.get('alert_type', 'combinado'))
        
        # Cargar configuración de notificaciones personalizadas
        custom_notif = task_data.get('custom_notification')
        if custom_notif:
            self.use_custom_notification.set(True)
            self.custom_sound_enabled.set(custom_notif.get('sound_enabled', True))
            self.custom_sound_file.set(custom_notif.get('sound_file', ''))
            self.custom_msg_high.set(custom_notif.get('message_high', '🚀 Afinidad ALTA aplicada'))
            self.custom_msg_low.set(custom_notif.get('message_low', '💚 Afinidad BAJA aplicada'))
            self.custom_show_process.set(custom_notif.get('show_process_name', True))
            self.custom_duration.set(custom_notif.get('duration', 3000))
            self.custom_position.set(custom_notif.get('position', 'top-right'))
            self.toggle_notification_config()  # Mostrar configuración
        else:
            self.use_custom_notification.set(False)
    
    def validate_input(self):
        """Valida la entrada del usuario"""
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "El nombre de la tarea es obligatorio")
            return False
        
        if not self.process_var.get().strip():
            messagebox.showerror("Error", "El nombre del proceso es obligatorio")
            return False
        
        if not self.hotkey_var.get().strip():
            messagebox.showerror("Error", "La combinación de teclas es obligatoria")
            return False
        
        high_selected = [i for i, var in enumerate(self.high_cpu_vars) if var.get()]
        if not high_selected:
            messagebox.showerror("Error", "Debe seleccionar al menos una CPU para afinidad alta")
            return False
        
        low_selected = [i for i, var in enumerate(self.low_cpu_vars) if var.get()]
        if not low_selected:
            messagebox.showerror("Error", "Debe seleccionar al menos una CPU para afinidad baja")
            return False
        
        return True
    
    def toggle_notification_config(self):
        """Muestra u oculta la configuración personalizada de notificaciones"""
        if self.use_custom_notification.get():
            self.custom_notif_frame.pack(fill=tk.X, pady=(10, 15))
        else:
            self.custom_notif_frame.pack_forget()
    
    def select_custom_sound(self):
        """Selecciona un archivo de sonido personalizado para la tarea"""
        filetypes = [
            ("Archivos de sonido", "*.wav *.mp3 *.ogg"),
            ("WAV", "*.wav"),
            ("MP3", "*.mp3"),
            ("OGG", "*.ogg"),
            ("Todos los archivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de sonido",
            filetypes=filetypes
        )
        
        if filename:
            self.custom_sound_file.set(filename)
    
    def test_custom_notification(self):
        """Prueba la notificación personalizada configurada"""
        # Simular configuración temporal
        temp_config = {
            'sound_enabled': self.custom_sound_enabled.get(),
            'sound_file': self.custom_sound_file.get() if self.custom_sound_file.get() else None,
            'message_high': self.custom_msg_high.get(),
            'message_low': self.custom_msg_low.get(),
            'show_process_name': self.custom_show_process.get(),
            'duration': self.custom_duration.get(),
            'position': self.custom_position.get()
        }
        
        # Guardar configuración original
        original_config = self.manager.notification_config.copy()
        
        try:
            # Aplicar configuración temporal
            self.manager.notification_config.update(temp_config)
            self.manager._last_process_name = "Proceso de Prueba"
            
            # Mostrar notificación de prueba
            self.manager.show_notification("", "high")
            
        finally:
            # Restaurar configuración original
            self.manager.notification_config = original_config
    
    def accept(self):
        """Acepta y guarda la configuración"""
        if not self.validate_input():
            return
        
        # Crear resultado básico
        self.result = {
            'name': self.name_var.get().strip(),
            'process_name': self.process_var.get().strip(),
            'hotkey': self.hotkey_var.get().strip(),
            'high_affinity': [i for i, var in enumerate(self.high_cpu_vars) if var.get()],
            'low_affinity': [i for i, var in enumerate(self.low_cpu_vars) if var.get()],
            'alert_type': self.alert_type.get()
        }
        
        # Agregar configuración de notificaciones si está habilitada
        if self.use_custom_notification.get():
            self.result['custom_notification'] = {
                'sound_enabled': self.custom_sound_enabled.get(),
                'sound_file': self.custom_sound_file.get() if self.custom_sound_file.get() else None,
                'message_high': self.custom_msg_high.get(),
                'message_low': self.custom_msg_low.get(),
                'show_process_name': self.custom_show_process.get(),
                'duration': self.custom_duration.get(),
                'position': self.custom_position.get()
            }
        else:
            self.result['custom_notification'] = None
        
        # Usar limpieza al cerrar correctamente
        if hasattr(self, 'canvas'):
            self.canvas.unbind_all("<MouseWheel>")
        self.dialog.unbind('<Key>')
        self.dialog.destroy()
    
    def cleanup_and_close(self):
        """Limpia recursos y cierra el diálogo"""
        if hasattr(self, 'canvas'):
            self.canvas.unbind_all("<MouseWheel>")
        self.dialog.unbind('<Key>')
        self.dialog.destroy()
    
    def cancel(self):
        """Cancela la configuración"""
        self.cleanup_and_close()


def main():
    """Función principal"""
    try:
        root = tk.Tk()
        app = AffinityManager(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error al inicializar la aplicación: {str(e)}")

if __name__ == "__main__":
    main()