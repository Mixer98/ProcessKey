"""
Gestión de tareas automatizadas para el Administrador de Afinidad
"""

import os
import json
import uuid
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import pygame
import winsound
import win32gui
import win32con
from typing import Dict, Any
import shutil
import keyboard
import traceback

# Inicializar pygame para el manejo de sonidos
pygame.mixer.init()

class TaskManager:
    """Gestor de tareas automatizadas"""
    
    def __init__(self, manager):
        self.manager = manager
        self.automated_tasks = {}
        self.hotkey_listeners = {}
        self.tasks_file = "automated_tasks.json"
        self.load_tasks()
        
    def log_message(self, message: str, level: str = "info"):
        """Registra un mensaje en el log del administrador principal"""
        if hasattr(self.manager, 'log_message'):
            self.manager.log_message(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def load_tasks(self):
        """Carga las tareas desde el archivo JSON"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.automated_tasks = data
                    
                # Configurar hotkeys para las tareas cargadas
                for task_id, task in self.automated_tasks.items():
                    if task.get('hotkey'):
                        self.setup_hotkey_listener(task['hotkey'], task_id)
                        
                self.log_message(f"Cargadas {len(self.automated_tasks)} tareas automatizadas", "success")
            else:
                self.automated_tasks = {}
                self.log_message("No se encontró archivo de tareas, iniciando con lista vacía", "info")
                
        except Exception as e:
            self.log_message(f"Error cargando tareas: {str(e)}", "error")
            self.automated_tasks = {}
    
    def save_tasks(self):
        """Guarda las tareas en el archivo JSON"""
        try:
            # Crear backup si existe el archivo
            if os.path.exists(self.tasks_file):
                shutil.copy2(self.tasks_file, f"{self.tasks_file}.backup")
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.automated_tasks, f, indent=2, ensure_ascii=False)
                
            self.log_message("Tareas guardadas correctamente", "success")
            return True
            
        except Exception as e:
            self.log_message(f"Error guardando tareas: {str(e)}", "error")
            return False
    
    def add_task(self, task_data: Dict[str, Any]) -> str:
        """Añade una nueva tarea"""
        try:
            task_id = str(uuid.uuid4())
            self.automated_tasks[task_id] = task_data
            
            # Configurar hotkey si existe
            if task_data.get('hotkey'):
                self.setup_hotkey_listener(task_data['hotkey'], task_id)
            
            # Guardar cambios
            if self.save_tasks():
                self.log_message(f"Tarea '{task_data['name']}' añadida correctamente", "success")
                return task_id
            else:
                # Si falla el guardado, remover de memoria
                del self.automated_tasks[task_id]
                if task_data.get('hotkey'):
                    self.remove_hotkey_listener(task_data['hotkey'])
                return None
                
        except Exception as e:
            self.log_message(f"Error añadiendo tarea: {str(e)}", "error")
            return None
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Actualiza una tarea existente"""
        try:
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada para actualizar", "error")
                return False
            
            old_task = self.automated_tasks[task_id]
            
            # Remover el hotkey anterior si existe
            if old_task.get('hotkey'):
                self.remove_hotkey_listener(old_task['hotkey'])
            
            # Actualizar la tarea
            self.automated_tasks[task_id] = task_data
            
            # Configurar nuevo hotkey si existe
            if task_data.get('hotkey'):
                self.setup_hotkey_listener(task_data['hotkey'], task_id)
            
            # Guardar cambios
            if self.save_tasks():
                self.log_message(f"Tarea '{task_data['name']}' actualizada correctamente", "success")
                return True
            else:
                # Revertir cambios si falla el guardado
                self.automated_tasks[task_id] = old_task
                if old_task.get('hotkey'):
                    self.setup_hotkey_listener(old_task['hotkey'], task_id)
                return False
                
        except Exception as e:
            self.log_message(f"Error actualizando tarea: {str(e)}", "error")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea"""
        try:
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada para eliminar", "error")
                return False
            
            task = self.automated_tasks[task_id]
            
            # Remover hotkey si existe
            if task.get('hotkey'):
                self.remove_hotkey_listener(task['hotkey'])
            
            # Eliminar de memoria
            del self.automated_tasks[task_id]
            
            # Guardar cambios
            if self.save_tasks():
                self.log_message(f"Tarea '{task['name']}' eliminada correctamente", "success")
                return True
            else:
                # Revertir si falla el guardado
                self.automated_tasks[task_id] = task
                if task.get('hotkey'):
                    self.setup_hotkey_listener(task['hotkey'], task_id)
                return False
                
        except Exception as e:
            self.log_message(f"Error eliminando tarea: {str(e)}", "error")
            return False
    
    def normalize_hotkey(self, hotkey: str) -> str:
        """Normaliza el formato del hotkey de tkinter al formato de la librería keyboard"""
        if not hotkey:
            return ""
        
        # Mapeo de teclas de tkinter a formato keyboard
        key_mapping = {
            'control_l': 'ctrl',
            'control_r': 'ctrl', 
            'alt_l': 'alt',
            'alt_r': 'alt',
            'shift_l': 'shift',
            'shift_r': 'shift',
        }
        
        keys = hotkey.split('+')
        normalized_keys = []
        
        for key in keys:
            key_lower = key.lower()
            if key_lower in key_mapping:
                normalized_keys.append(key_mapping[key_lower])
            else:
                normalized_keys.append(key_lower)
        
        return '+'.join(normalized_keys)

    def setup_hotkey_listener(self, hotkey: str, task_id: str):
        """Configura un listener para el hotkey de una tarea"""
        try:
            # Normalizar el hotkey
            normalized_hotkey = self.normalize_hotkey(hotkey)
            self.log_message(f"Hotkey original: '{hotkey}' -> Normalizado: '{normalized_hotkey}'", "info")
            
            # Remover listener existente si lo hay
            if normalized_hotkey in self.hotkey_listeners:
                self.remove_hotkey_listener(normalized_hotkey)
            
            # Crear función de callback
            def callback():
                self.log_message(f"Hotkey '{normalized_hotkey}' activado - ejecutando tarea {task_id}", "info")
                self.execute_task(task_id)
            
            # Registrar hotkey
            keyboard.add_hotkey(normalized_hotkey, callback, suppress=True)
            self.hotkey_listeners[normalized_hotkey] = callback
            
            self.log_message(f"Hotkey '{normalized_hotkey}' registrado correctamente", "success")
            
        except Exception as e:
            self.log_message(f"Error configurando hotkey: {str(e)}", "error")
    
    def remove_hotkey_listener(self, hotkey: str):
        """Elimina un listener de hotkey"""
        try:
            normalized_hotkey = self.normalize_hotkey(hotkey)
            if normalized_hotkey in self.hotkey_listeners:
                keyboard.remove_hotkey(normalized_hotkey)
                del self.hotkey_listeners[normalized_hotkey]
                self.log_message(f"Hotkey '{normalized_hotkey}' eliminado correctamente", "success")
        except Exception as e:
            self.log_message(f"Error eliminando hotkey: {str(e)}", "error")
    
    def execute_task(self, task_id: str):
        """Ejecuta una tarea automatizada"""
        try:
            self.log_message(f"Iniciando ejecución de tarea: {task_id}", "info")
            
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada", "error")
                return
            
            task = self.automated_tasks[task_id]
            process_name = task['process_name']
            target_affinity = task['target_affinity']
            
            self.log_message(f"Buscando proceso: {process_name}", "info")
            
            # Buscar el proceso por nombre
            found_process = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        found_process = True
                        self.log_message(f"Proceso encontrado: {process_name} (PID: {proc.pid})", "info")
                        
                        # Aplicar afinidad
                        proc.cpu_affinity(target_affinity)
                        
                        # Mostrar notificación
                        cpu_list = ', '.join([f"CPU{cpu}" for cpu in target_affinity])
                        message = f"Afinidad aplicada a {process_name}\nCPUs: {cpu_list}"
                        self.manager.show_notification(message)
                        
                        # Reproducir sonido si está configurado
                        if task.get('custom_sound', {}).get('enabled', False):
                            sound_file = task['custom_sound']['file']
                            if sound_file and os.path.exists(sound_file):
                                try:
                                    if sound_file.lower().endswith('.mp3'):
                                        pygame.mixer.music.load(sound_file)
                                        pygame.mixer.music.play()
                                    else:
                                        sound = pygame.mixer.Sound(sound_file)
                                        sound.play()
                                except Exception as e:
                                    self.log_message(f"Error reproduciendo sonido: {str(e)}", "warning")
                        
                        self.log_message(
                            f"Tarea ejecutada: {task['name']}, Proceso: {process_name}, "
                            f"Afinidad: {cpu_list}",
                            "success"
                        )
                        return
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not found_process:
                self.log_message(f"Proceso {process_name} no encontrado", "warning")
            
        except Exception as e:
            self.log_message(f"Error ejecutando tarea: {str(e)}", "error")

    def edit_task_dialog(self, task_id: str = None):
        """Muestra el diálogo para editar una tarea existente"""
        if not task_id:
            messagebox.showwarning("Advertencia", "Debe seleccionar una tarea para editar")
            return
            
        if task_id not in self.automated_tasks:
            messagebox.showerror("Error", "Tarea no encontrada")
            return
            
        try:
            # Obtener datos de la tarea existente
            task_data = self.automated_tasks[task_id].copy()
            
            # Mostrar el diálogo de edición
            dialog = TaskDialog(self.manager.root, task_data, is_edit=True)
            self.manager.root.wait_window(dialog.dialog)
            
            if dialog.result:
                # Actualizar la tarea
                self.update_task(task_id, dialog.result)
                
                # Actualizar la vista de tareas
                if hasattr(self.manager, 'ui'):
                    self.manager.ui.refresh_tasks_display(self.manager)
                    
                self.log_message(f"Tarea '{dialog.result['name']}' actualizada correctamente", "success")
                
        except Exception as e:
            self.log_message(f"Error editando tarea: {str(e)}", "error")
            messagebox.showerror("Error", f"Error editando tarea: {str(e)}")

    def execute_automated_task(self, task_id: str = None):
        """Ejecuta manualmente una tarea automatizada para pruebas"""
        if not task_id:
            messagebox.showwarning("Advertencia", "Debe seleccionar una tarea para probar")
            return
            
        try:
            self.log_message(f"Ejecutando tarea manualmente: {task_id}", "info")
            self.execute_task(task_id)
            
        except Exception as e:
            self.log_message(f"Error ejecutando tarea: {str(e)}", "error")
            messagebox.showerror("Error", f"Error ejecutando tarea: {str(e)}")

    def delete_task_with_confirmation(self, task_id: str = None):
        """Elimina una tarea con confirmación del usuario"""
        if not task_id:
            messagebox.showwarning("Advertencia", "Debe seleccionar una tarea para eliminar")
            return
            
        if task_id not in self.automated_tasks:
            messagebox.showerror("Error", "Tarea no encontrada")
            return
            
        try:
            task_name = self.automated_tasks[task_id]['name']
            
            # Confirmar eliminación
            result = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Está seguro de eliminar la tarea '{task_name}'?\n\n"
                "Esta acción no se puede deshacer."
            )
            
            if result:
                if self.delete_task(task_id):
                    # Actualizar la vista de tareas
                    if hasattr(self.manager, 'ui'):
                        self.manager.ui.refresh_tasks_display(self.manager)
                        
        except Exception as e:
            self.log_message(f"Error eliminando tarea: {str(e)}", "error")
            messagebox.showerror("Error", f"Error eliminando tarea: {str(e)}")


class TaskDialog:
    """Diálogo para crear o editar tareas"""
    def __init__(self, parent, task_data=None, is_edit=False):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Editar Tarea" if is_edit else "Crear Tarea Automatizada")
        self.dialog.grab_set()
        
        # Hacer el diálogo modal y centrarlo
        self.dialog.transient(parent)
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configurar el diálogo
        self.dialog.resizable(False, False)
        self.parent = parent
        self.task_data = task_data or {}
        self.result = None
        self.listening_for_hotkey = False
        self.cpu_count = psutil.cpu_count()
        
        self.setup_dialog()
        
        # Centrar el diálogo después de crearlo
        self.center_dialog()
        
    def setup_dialog(self):
        """Configura la interfaz del diálogo"""
        frame = ttk.Frame(self.dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar variables
        self.name_var = tk.StringVar(value=self.task_data.get('name', ''))
        self.process_var = tk.StringVar(value=self.task_data.get('process_name', ''))
        self.hotkey_key_count_var = tk.IntVar(value=2)  # Por defecto 2 teclas
        self.custom_sound_var = tk.BooleanVar(value=self.task_data.get('custom_sound', {}).get('enabled', False))
        self.sound_file_var = tk.StringVar(value=self.task_data.get('sound_file', ''))
        
        current_row = 0
        
        # Nombre de la tarea
        ttk.Label(frame, text="Nombre de la tarea:").grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Nombre del proceso
        ttk.Label(frame, text="Nombre del proceso (ej: notepad.exe):").grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        process_entry = ttk.Entry(frame, textvariable=self.process_var, width=40)
        process_entry.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Configuración de hotkey simplificada
        hotkey_frame = ttk.LabelFrame(frame, text="Configuración de Hotkey", padding="10")
        hotkey_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Selector de número de teclas
        ttk.Label(hotkey_frame, text="Número de teclas:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        keys_spin = ttk.Spinbox(hotkey_frame, from_=1, to=4, textvariable=self.hotkey_key_count_var, width=5, command=self.update_hotkey_fields)
        keys_spin.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Botón para actualizar campos
        update_btn = ttk.Button(hotkey_frame, text="Actualizar campos", command=self.update_hotkey_fields)
        update_btn.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # Frame para los campos de hotkey
        self.hotkey_fields_frame = ttk.Frame(hotkey_frame)
        self.hotkey_fields_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Crear los campos iniciales
        self.hotkey_entries = []
        self.update_hotkey_fields()
        
        # Pre-llenar hotkeys si es edición
        if self.task_data.get('hotkey'):
            self.populate_hotkey_fields(self.task_data['hotkey'])
        
        # Configuración de afinidad de CPU
        cpu_frame = ttk.LabelFrame(frame, text="Afinidad de CPU", padding="10")
        cpu_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Variables para las CPUs
        self.cpu_affinity_vars = []
        for i in range(self.cpu_count):
            var = tk.BooleanVar()
            # Pre-seleccionar CPUs si es edición
            if self.task_data.get('target_affinity') and i in self.task_data['target_affinity']:
                var.set(True)
            self.cpu_affinity_vars.append(var)
        
        # Crear checkboxes para CPUs en múltiples columnas
        cols = 4  # 4 columnas
        for i, var in enumerate(self.cpu_affinity_vars):
            row = i // cols + 1
            col = i % cols
            cb = ttk.Checkbutton(cpu_frame, text=f"CPU {i}", variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=(0, 10), pady=2)
        
        # Botones para seleccionar/deseleccionar todas
        button_frame = ttk.Frame(cpu_frame)
        button_frame.grid(row=0, column=0, columnspan=cols, sticky=tk.W, pady=(0, 10))
        
        select_all_btn = ttk.Button(button_frame, text="Seleccionar todas", 
                                  command=lambda: self.select_all_cpus(self.cpu_affinity_vars))
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        deselect_all_btn = ttk.Button(button_frame, text="Deseleccionar todas",
                                    command=lambda: self.deselect_all_cpus(self.cpu_affinity_vars))
        deselect_all_btn.pack(side=tk.LEFT)
        
        # Configuración de alertas
        alerts_frame = ttk.LabelFrame(frame, text="Tipos de Alerta", padding="10")
        alerts_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        self.alert_vars = {}
        alert_types = [
            ('notification', 'Notificación en pantalla'),
            ('system_sound', 'Sonido del sistema'),
            ('custom_sound', 'Sonido personalizado'),
            ('log_message', 'Mensaje en log')
        ]
        
        for i, (key, label) in enumerate(alert_types):
            var = tk.BooleanVar()
            # Pre-seleccionar si es edición
            if self.task_data.get('alerts') and key in self.task_data['alerts']:
                var.set(True)
            elif not self.task_data.get('alerts'):  # Si es nueva tarea, activar por defecto
                var.set(True)
            
            self.alert_vars[key] = var
            cb = ttk.Checkbutton(alerts_frame, text=label, variable=var)
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 10), pady=2)
        
        # Configuración de sonido personalizado
        sound_frame = ttk.LabelFrame(frame, text="Sonido Personalizado", padding="10")
        sound_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        sound_enable_cb = ttk.Checkbutton(sound_frame, text="Habilitar sonido personalizado", 
                                        variable=self.custom_sound_var)
        sound_enable_cb.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(sound_frame, text="Archivo de sonido:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        sound_entry = ttk.Entry(sound_frame, textvariable=self.sound_file_var, width=30)
        sound_entry.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        browse_btn = ttk.Button(sound_frame, text="Examinar...", command=self.browse_sound_file)
        browse_btn.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=(0, 5))
        
        test_sound_btn = ttk.Button(sound_frame, text="Probar", command=self.test_sound)
        test_sound_btn.grid(row=2, column=2, sticky=tk.W, padx=(5, 0), pady=(0, 5))
        
        # Botones del diálogo
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        save_btn = ttk.Button(button_frame, text="Guardar", command=self.validate_and_save)
        save_btn.pack(side=tk.RIGHT)
    
    def update_hotkey_fields(self):
        """Actualiza los campos de hotkey según el número seleccionado"""
        # Limpiar campos existentes
        for widget in self.hotkey_fields_frame.winfo_children():
            widget.destroy()
        
        self.hotkey_entries = []
        num_keys = self.hotkey_key_count_var.get()
        
        for i in range(num_keys):
            # Label
            ttk.Label(self.hotkey_fields_frame, text=f"Tecla {i+1}:").grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Entry
            entry = ttk.Entry(self.hotkey_fields_frame, width=15)
            entry.grid(row=i, column=1, sticky=tk.W, padx=(0, 10), pady=2)
            entry.bind('<KeyPress>', lambda e, idx=i: self.capture_key(e, idx))
            entry.bind('<Button-1>', lambda e, idx=i: self.focus_entry(e, idx))
            self.hotkey_entries.append(entry)
            
            # Botón para capturar
            capture_btn = ttk.Button(self.hotkey_fields_frame, text="Capturar", 
                                   command=lambda idx=i: self.start_key_capture(idx))
            capture_btn.grid(row=i, column=2, sticky=tk.W, padx=(5, 0), pady=2)
    
    def populate_hotkey_fields(self, hotkey_string):
        """Rellena los campos de hotkey con un string existente"""
        if not hotkey_string:
            return
            
        keys = hotkey_string.split('+')
        
        # Ajustar el número de campos si es necesario
        if len(keys) != self.hotkey_key_count_var.get():
            self.hotkey_key_count_var.set(len(keys))
            self.update_hotkey_fields()
        
        # Rellenar los campos
        for i, key in enumerate(keys):
            if i < len(self.hotkey_entries):
                self.hotkey_entries[i].delete(0, tk.END)
                self.hotkey_entries[i].insert(0, key.strip())
    
    def focus_entry(self, event, idx):
        """Maneja el foco en una entry de hotkey"""
        self.hotkey_entries[idx].focus_set()
    
    def start_key_capture(self, idx):
        """Inicia la captura de una tecla para un campo específico"""
        entry = self.hotkey_entries[idx]
        entry.delete(0, tk.END)
        entry.insert(0, "Presiona una tecla...")
        entry.focus_set()
        
        # Configurar para capturar la próxima tecla
        self.listening_for_hotkey = True
        self.current_capture_idx = idx
    
    def capture_key(self, event, idx):
        """Captura una tecla presionada"""
        if not self.listening_for_hotkey or idx != getattr(self, 'current_capture_idx', -1):
            return "break"
            
        key_str = self.get_key_str(event)
        if key_str:
            entry = self.hotkey_entries[idx]
            entry.delete(0, tk.END)
            entry.insert(0, key_str)
            
            self.listening_for_hotkey = False
            
            # Auto-avanzar al siguiente campo si existe
            if idx + 1 < len(self.hotkey_entries):
                self.hotkey_entries[idx + 1].focus_set()
        
        return "break"

    def get_hotkey_combination(self):
        """Obtiene la combinación de teclas desde los campos"""
        keys = [e.get().strip() for e in self.hotkey_entries if e.get().strip() and e.get().strip() != "Presiona una tecla..."]
        return '+'.join(keys)

    def browse_sound_file(self):
        """Permite al usuario seleccionar un archivo de sonido"""
        file_path = tk.filedialog.askopenfilename(
            title="Seleccionar archivo de sonido",
            filetypes=[
                ("Archivos de sonido", "*.wav *.mp3"),
                ("Todos los archivos", "*.*")
            ]
        )
        if file_path:
            self.sound_file_var.set(file_path)
            
    def test_sound(self):
        """Reproduce el sonido seleccionado para prueba"""
        sound_file = self.sound_file_var.get()
        if not sound_file:
            messagebox.showwarning("Advertencia", "Primero seleccione un archivo de sonido")
            return
            
        if not os.path.exists(sound_file):
            messagebox.showerror("Error", "El archivo de sonido no existe")
            return
            
        try:
            if sound_file.lower().endswith('.mp3'):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
            else:
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
        except Exception as e:
            messagebox.showerror("Error", f"Error reproduciendo el sonido: {str(e)}")
    
    def validate_and_save(self):
        """Valida y guarda los datos de la tarea"""
        try:
            name = self.name_var.get().strip()
            process = self.process_var.get().strip()
            hotkey = self.get_hotkey_combination()
            
            # Validaciones básicas
            if not all([name, process]):
                messagebox.showwarning("Error", "El nombre y el proceso son obligatorios")
                return
            
            if not hotkey:
                messagebox.showwarning("Error", "Debe capturar una combinación de teclas")
                return
            
            # Obtener CPUs seleccionadas
            target_affinity = [i for i, var in enumerate(self.cpu_affinity_vars) if var.get()]
            
            if not target_affinity:
                messagebox.showwarning("Error", "Debe seleccionar al menos una CPU")
                return
            
            # Verificar que al menos un tipo de alerta esté seleccionado
            selected_alerts = [k for k, v in self.alert_vars.items() if v.get()]
            if not selected_alerts:
                messagebox.showwarning("Error", "Debe seleccionar al menos un tipo de alerta")
                return
            
            # Guardar resultado
            self.result = {
                'name': name,
                'process_name': process,
                'hotkey': hotkey,
                'target_affinity': target_affinity,
                'alerts': selected_alerts,
                'custom_sound': {'enabled': self.custom_sound_var.get()},
                'sound_file': self.sound_file_var.get()
            }
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la tarea: {str(e)}")
            print(f"Error detallado: {traceback.format_exc()}")  # Para debugging

    def center_dialog(self):
        """Centra el diálogo en la pantalla"""
        self.dialog.update_idletasks()
        
        # Obtener dimensiones de la pantalla
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        
        # Obtener dimensiones del diálogo
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calcular posición
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - dialog_width) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - dialog_height) // 2
        
        # Asegurar que el diálogo no se salga de la pantalla
        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))
        
        self.dialog.geometry(f"+{x}+{y}")
        
    def on_close(self):
        """Maneja el cierre del diálogo"""
        if self.listening_for_hotkey:
            self.listening_for_hotkey = False
        self.dialog.destroy()

    def select_all_cpus(self, vars_list):
        """Selecciona todas las CPUs en el grupo de checkboxes"""
        for var in vars_list:
            var.set(True)
            
    def deselect_all_cpus(self, vars_list):
        """Deselecciona todas las CPUs en el grupo de checkboxes"""
        for var in vars_list:
            var.set(False)
    
    def get_key_str(self, key):
        """Convierte una tecla en su representación como string"""
        try:
            # Para teclas normales que tienen un caracter imprimible
            if hasattr(key, 'char') and key.char:
                if key.char.isprintable():
                    return key.char.lower()
                return None
                
            # Para teclas especiales usando keysym
            if hasattr(key, 'keysym'):
                key_name = key.keysym.lower()
            else:
                key_name = str(key).lower()
            
            # Mapeo de teclas especiales
            key_mapping = {
                'control_l': 'ctrl', 'control_r': 'ctrl',
                'alt_l': 'alt', 'alt_r': 'alt', 
                'shift_l': 'shift', 'shift_r': 'shift',
                'space': 'space',
                'return': 'enter',
                'escape': 'escape',
                'caps_lock': 'capslock',
                'page_up': 'pageup',
                'page_down': 'pagedown',
                'backspace': 'backspace',
                'delete': 'delete',
                'tab': 'tab',
                'num_lock': 'numlock',
                'scroll_lock': 'scrolllock',
                'print': 'printscreen',
                'home': 'home',
                'end': 'end',
                'insert': 'insert',
                'pause': 'pause',
                'menu': 'menu',
                'up': 'up',
                'down': 'down', 
                'left': 'left',
                'right': 'right',
            }
            
            # Agregar teclas de función (F1-F24)
            key_mapping.update({f'f{i}': f'f{i}' for i in range(1, 25)})
            
            return key_mapping.get(key_name, key_name)
            
        except Exception as e:
            print(f"Error en get_key_str: {e}")
            return str(key.keysym if hasattr(key, 'keysym') else key).lower()

    def save_automated_tasks(self):
        """Alias de save_tasks para compatibilidad"""
        return self.save_tasks()


