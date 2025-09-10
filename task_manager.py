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
        
        # Nombre de la tarea
        ttk.Label(frame, text="Nombre de la tarea:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.task_data.get('name', ''))
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Proceso objetivo
        ttk.Label(frame, text="Proceso objetivo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.process_var = tk.StringVar(value=self.task_data.get('process_name', ''))
        process_entry = ttk.Entry(frame, textvariable=self.process_var, width=40)
        process_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Hotkey
        ttk.Label(frame, text="Teclas de acceso rápido:").grid(row=2, column=0, sticky=tk.W, pady=5)
        hotkey_frame = ttk.Frame(frame)
        hotkey_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)

        # Selector de cantidad de teclas
        ttk.Label(hotkey_frame, text="Cantidad de teclas:").pack(side=tk.LEFT)
        self.num_keys_var = tk.IntVar(value=2)
        num_keys_spin = ttk.Spinbox(hotkey_frame, from_=2, to=5, width=3, textvariable=self.num_keys_var, command=self.update_hotkey_fields, state='readonly')
        num_keys_spin.pack(side=tk.LEFT, padx=(5, 10))

        # Frame para los campos de teclas
        self.keys_fields_frame = ttk.Frame(hotkey_frame)
        self.keys_fields_frame.pack(side=tk.LEFT)
        self.hotkey_entries = []
        self.update_hotkey_fields()

        ttk.Label(frame, text="(Presione cada tecla, una por campo. Ej: Ctrl, Alt, K)", font=('Arial', 8)).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Afinidad
        ttk.Label(frame, text="CPUs a utilizar:", font=('Arial', 9, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        
        # Frame para los checkboxes de afinidad
        cpu_frame = ttk.LabelFrame(frame, text="Seleccione las CPUs que usará el proceso")
        cpu_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Frame para los botones de selección
        btn_frame = ttk.Frame(cpu_frame)
        btn_frame.grid(row=0, column=0, columnspan=4, pady=(0, 5), sticky=tk.W)
        
        ttk.Button(btn_frame, text="Seleccionar Todas", 
                  command=lambda: self.select_all_cpus(self.cpu_affinity_vars)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deseleccionar Todas", 
                  command=lambda: self.deselect_all_cpus(self.cpu_affinity_vars)).pack(side=tk.LEFT)
        
        # Checkboxes para afinidad
        self.cpu_affinity_vars = []
        target_cpus = self.task_data.get('target_affinity', [])
        
        for i in range(self.cpu_count):
            var = tk.BooleanVar(value=i in target_cpus)
            self.cpu_affinity_vars.append(var)
            ttk.Checkbutton(cpu_frame, text=f"CPU{i}", variable=var).grid(
                row=(i // 4) + 1, column=i % 4, padx=5, pady=2)
        
        # Frame para el tipo de alerta
        alert_section = ttk.LabelFrame(frame, text="🔔 Configuración de Alertas", padding="10")
        alert_section.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=5)
        
        ttk.Label(alert_section, text="Seleccione los tipos de alerta:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
            
        # Frame para los controles de alerta
        alert_frame = ttk.Frame(alert_section)
        alert_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Variables para cada tipo de alerta
        self.alert_vars = {
            'notification': tk.BooleanVar(value=True),
            'sound': tk.BooleanVar(value=True),
            'tray': tk.BooleanVar(value=True),
            'flash': tk.BooleanVar(value=False),
        }
        
        # Checkboxes para cada tipo de alerta
        alerts = [
            ("🔔 Notificación en pantalla", 'notification', 0, 0),
            ("🔊 Sonido de alerta", 'sound', 0, 1),
            ("💬 Icono en bandeja", 'tray', 1, 0),
            ("⚡ Parpadeo de ventana", 'flash', 1, 1),
        ]
        
        for text, key, row, col in alerts:
            ttk.Checkbutton(alert_frame, text=text, variable=self.alert_vars[key]).grid(
                row=row, column=col, padx=10, pady=5, sticky=tk.W)
            
        # Frame para sonidos personalizados
        sound_frame = ttk.LabelFrame(alert_section, text="🎵 Sonido Personalizado")
        sound_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10,5), padx=5)
        
        self.custom_sound_var = tk.BooleanVar(value=self.task_data.get('custom_sound', {}).get('enabled', False))
        ttk.Checkbutton(sound_frame, text="Usar sonido personalizado", 
                       variable=self.custom_sound_var).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                       
        self.sound_file_var = tk.StringVar(value=self.task_data.get('sound_file', ''))
        file_frame = ttk.Frame(sound_frame)
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.sound_file_entry = ttk.Entry(file_frame, textvariable=self.sound_file_var, width=30)
        self.sound_file_entry.pack(side=tk.LEFT, padx=(0,5))
        
        ttk.Button(file_frame, text="Examinar", 
                  command=self.browse_sound_file).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Probar", 
                  command=self.test_sound).pack(side=tk.LEFT, padx=(5,0))
        
        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Guardar", command=self.validate_and_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def update_hotkey_fields(self):
        """Actualiza los campos de entrada de teclas según la cantidad seleccionada y activa la captura"""
        for widget in self.keys_fields_frame.winfo_children():
            widget.destroy()
        self.hotkey_entries = []
        for i in range(self.num_keys_var.get()):
            entry = ttk.Entry(self.keys_fields_frame, width=8, justify='center', state='readonly')
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind('<FocusIn>', lambda e, idx=i: self.start_key_capture(idx))
            self.hotkey_entries.append(entry)
        # Opcional: poner foco en el primer campo
        self.hotkey_entries[0].config(state='normal')
        self.hotkey_entries[0].focus_set()

    def start_key_capture(self, idx):
        """Activa la captura de una tecla para el campo idx"""
        entry = self.hotkey_entries[idx]
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.bind('<KeyPress>', lambda event, i=idx: self.on_key_press(event, i))

    def on_key_press(self, event, idx):
        """Captura la tecla presionada y la pone en el campo correspondiente"""
        key = event.keysym.title()
        entry = self.hotkey_entries[idx]
        entry.delete(0, tk.END)
        entry.insert(0, key)
        entry.config(state='readonly')
        entry.unbind('<KeyPress>')
        # Pasar foco al siguiente campo si existe
        if idx + 1 < len(self.hotkey_entries):
            self.hotkey_entries[idx + 1].config(state='normal')
            self.hotkey_entries[idx + 1].focus_set()
        # Si es el último, opcional: volver al primero o dejar así

    def get_hotkey_combination(self):
        """Obtiene la combinación de teclas desde los campos"""
        keys = [e.get().strip() for e in self.hotkey_entries if e.get().strip()]
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
                
            # Validar hotkey
            is_valid, error_msg = self.validate_hotkey(hotkey)
            if not is_valid:
                messagebox.showerror("Error", error_msg or "Combinación de teclas inválida")
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
            self.stop_hotkey_capture()
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
                
            # Para teclas especiales
            if hasattr(key, '_name_'):
                key_name = key._name_.lower()
            else:
                key_name = str(key).replace('Key.', '').lower()
            
            # Mapeo de teclas especiales
            key_mapping = {
                'ctrl_l': 'ctrl', 'ctrl_r': 'ctrl',
                'alt_l': 'alt', 'alt_r': 'alt',
                'shift_l': 'shift', 'shift_r': 'shift',
                'space': 'spacebar',
                'return': 'enter',
                'esc': 'escape',
                'caps_lock': 'capslock',
                'page_up': 'pageup',
                'page_down': 'pagedown',
                'backspace': 'backspace',
                'delete': 'delete',
                'tab': 'tab',
                'num_lock': 'numlock',
                'scroll_lock': 'scrolllock',
                'print_screen': 'printscreen',
                'home': 'home',
                'end': 'end',
                'insert': 'insert',
                'pause': 'pause',
                'menu': 'menu',
                'up': '↑',
                'down': '↓',
                'left': '←',
                'right': '→',
            }
            
            # Mapeo del teclado numérico
            if hasattr(key, 'vk') and 96 <= key.vk <= 105:  # Teclas numéricas del teclado numérico
                return str(key.vk - 96)
            
            # Mapeo de números normales
            if key_name.isdigit():
                return key_name
                
            # Agregar teclas de función (F1-F24)
            key_mapping.update({f'f{i}': f'f{i}' for i in range(1, 25)})
            
            return key_mapping.get(key_name, key_name)
            
        except Exception as e:
            print(f"Error en get_key_str: {e}")
            return None

    def validate_hotkey(self, hotkey):
        """Valida que el hotkey sea válido y no conflictivo"""
        if not hotkey:
            return False, "La combinación de teclas no puede estar vacía"
            
        keys = [k.lower() for k in hotkey.split("+")]  # Convertir a minúsculas para comparar
        
        # Debe tener al menos un modificador (ctrl, alt, shift)
        modifiers = ['ctrl', 'alt', 'shift', 'control']
        if not any(mod in keys for mod in modifiers):
            return False, "La combinación debe incluir al menos una tecla modificadora (Ctrl, Alt, Shift)"
            
        # Debe tener al menos una tecla no modificadora
        non_modifiers = [k for k in keys if k not in modifiers]
        if not non_modifiers:
            return False, "La combinación debe incluir al menos una tecla además de los modificadores"
        
        # No debe ser una combinación peligrosa o reservada
        dangerous_combinations = [
            ['ctrl', 'alt', 'delete'],
            ['ctrl', 'alt', 'supr'],
            ['ctrl', 'shift', 'escape'],
            ['win'],
            ['cmd'],
        ]
        
        # Verificar combinaciones peligrosas
        for dc in dangerous_combinations:
            if all(k in keys for k in dc):
                return False, "Combinación de teclas reservada del sistema"
        
        # Número máximo de teclas (modificadores + 3 teclas adicionales)
        if len(keys) > 6:  # 3 modificadores posibles + 3 teclas adicionales
            return False, "La combinación no puede tener más de 6 teclas en total"
            
        return True, ""

class TaskManager:
    """Gestor de tareas automatizadas"""
    def __init__(self, manager):
        self.manager = manager
        self.tasks_file = "automated_tasks.json"
        self.automated_tasks = {}
        self.hotkey_listeners = {}
        self.ui_ready = False
        
        # Asegurarnos de que el archivo de tareas existe
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        
        # Cargar tareas al iniciar
        self.load_automated_tasks()
    
    def load_automated_tasks(self):
        """Carga las tareas automatizadas desde el archivo"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.automated_tasks = json.load(f)
                    
                # Configurar hotkeys para las tareas cargadas
                for task_id, task_data in self.automated_tasks.items():
                    self.setup_hotkey_listener(task_data['hotkey'], task_id)
                    
                self.log_message("Tareas automatizadas cargadas correctamente", "success")
            else:
                self.log_message("No se encontró archivo de tareas, se creará uno nuevo")
                self.save_automated_tasks()
        except Exception as e:
            self.log_message(f"Error cargando tareas: {str(e)}", "error")
            self.automated_tasks = {}

    def save_automated_tasks(self):
        """Guarda las tareas automatizadas en el archivo"""
        try:
            # Crear backup del archivo existente
            if os.path.exists(self.tasks_file):
                backup_file = self.tasks_file + ".backup"
                shutil.copy2(self.tasks_file, backup_file)
            
            # Guardar tareas
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.automated_tasks, f, indent=4, ensure_ascii=False)
                
            self.log_message("Tareas guardadas correctamente", "success")
        except Exception as e:
            self.log_message(f"Error guardando tareas: {str(e)}", "error")
    
    def log_message(self, message: str, level: str = "info"):
        """Sistema de logging temporal hasta que la UI esté lista"""
        if hasattr(self.manager, 'log_message'):
            self.manager.log_message(message, level)
        else:
            prefix = {
                "error": "❌",
                "warning": "⚠️",
                "success": "✅",
                "info": "ℹ️"
            }.get(level, "ℹ️")
            print(f"{prefix} {message}")
    
    def add_task(self, task_data: Dict[str, Any]) -> bool:
        """Agrega una nueva tarea automatizada"""
        try:
            # Generar ID único para la tarea
            task_id = str(uuid.uuid4())
            
            # Agregar la tarea a la colección
            self.automated_tasks[task_id] = task_data
            
            # Configurar hotkey
            self.setup_hotkey_listener(task_data['hotkey'], task_id)
            
            # Guardar cambios
            self.save_automated_tasks()
            
            self.log_message(f"Tarea '{task_data['name']}' agregada correctamente", "success")
            return True
            
        except Exception as e:
            self.log_message(f"Error agregando tarea: {str(e)}", "error")
            return False
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Actualiza una tarea existente"""
        try:
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada", "error")
                return False
            
            # Eliminar el hotkey anterior
            old_hotkey = self.automated_tasks[task_id]['hotkey']
            self.remove_hotkey_listener(old_hotkey)
            
            # Actualizar datos
            self.automated_tasks[task_id] = task_data
            
            # Configurar nuevo hotkey
            self.setup_hotkey_listener(task_data['hotkey'], task_id)
            
            # Guardar cambios
            self.save_automated_tasks()
            
            self.log_message(f"Tarea '{task_data['name']}' actualizada correctamente", "success")
            return True
            
        except Exception as e:
            self.log_message(f"Error actualizando tarea: {str(e)}", "error")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea automatizada"""
        try:
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada", "error")
                return False
            
            # Eliminar hotkey
            hotkey = self.automated_tasks[task_id]['hotkey']
            self.remove_hotkey_listener(hotkey)
            
            # Eliminar tarea
            del self.automated_tasks[task_id]
            
            # Guardar cambios
            self.save_automated_tasks()
            
            self.log_message("Tarea eliminada correctamente", "success")
            return True
            
        except Exception as e:
            self.log_message(f"Error eliminando tarea: {str(e)}", "error")
            return False
    
    def setup_hotkey_listener(self, hotkey: str, task_id: str):
        """Configura un listener para el hotkey de una tarea"""
        try:
            # Remover listener existente si lo hay
            if hotkey in self.hotkey_listeners:
                self.remove_hotkey_listener(hotkey)
            
            # Crear función de callback
            def callback():
                self.execute_task(task_id)
            
            # Registrar hotkey
            keyboard.add_hotkey(hotkey, callback, suppress=True)
            self.hotkey_listeners[hotkey] = callback
            
            self.log_message(f"Hotkey '{hotkey}' registrado correctamente", "success")
            
        except Exception as e:
            self.log_message(f"Error configurando hotkey: {str(e)}", "error")
    
    def remove_hotkey_listener(self, hotkey: str):
        """Elimina un listener de hotkey"""
        try:
            if hotkey in self.hotkey_listeners:
                keyboard.remove_hotkey(hotkey)
                del self.hotkey_listeners[hotkey]
                self.log_message(f"Hotkey '{hotkey}' eliminado correctamente", "success")
        except Exception as e:
            self.log_message(f"Error eliminando hotkey: {str(e)}", "error")
    
    def execute_task(self, task_id: str):
        """Ejecuta una tarea automatizada"""
        try:
            if task_id not in self.automated_tasks:
                self.log_message(f"Tarea {task_id} no encontrada", "error")
                return
            
            task = self.automated_tasks[task_id]
            process_name = task['process_name']
            target_affinity = task['target_affinity']
            
            # Buscar el proceso por nombre
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
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
            
            self.log_message(f"Proceso {process_name} no encontrado", "warning")
            
        except Exception as e:
            self.log_message(f"Error ejecutando tarea: {str(e)}", "error")
