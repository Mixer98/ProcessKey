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
from pynput import keyboard as pynput_keyboard

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
        ttk.Label(frame, text="Tecla de acceso rápido:").grid(row=2, column=0, sticky=tk.W, pady=5)
        hotkey_frame = ttk.Frame(frame)
        hotkey_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.hotkey_var = tk.StringVar(value=self.task_data.get('hotkey', ''))
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.hotkey_var, width=20, state='readonly')
        self.hotkey_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        self.capture_btn = ttk.Button(hotkey_frame, text="Capturar", command=self.start_hotkey_capture)
        self.capture_btn.pack(side=tk.LEFT)
        
        ttk.Label(frame, text="(Haga clic en 'Capturar' y presione la combinación de teclas deseada)",
                 font=('Arial', 8)).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(0, 10))
        
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
        
        self.custom_sound_var = tk.BooleanVar(value=False)
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
        
    def start_hotkey_capture(self):
        """Inicia la captura de teclas"""
        if self.listening_for_hotkey:
            self.stop_hotkey_capture()
            return
            
        self.listening_for_hotkey = True
        self.hotkey_entry.config(state='normal')
        self.hotkey_var.set("Presione una combinación de teclas...")
        self.hotkey_entry.config(state='readonly')
        self.capture_btn.config(text="Cancelar")
        
        # Inicializar variables de captura
        self.pressed_keys = set()
        self.last_key_time = time.time()
        
        # Iniciar listener de teclado
        self.keyboard_listener = pynput_keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release)
        self.keyboard_listener.start()
        
        # Programar detención automática después de 10 segundos si no se ha capturado nada
        self.auto_stop_timer = self.dialog.after(10000, self.auto_stop_capture)
    
    def auto_stop_capture(self):
        """Detiene automáticamente la captura si no hay actividad"""
        if self.listening_for_hotkey:
            current_time = time.time()
            if not self.pressed_keys and (current_time - self.last_key_time) > 2:
                self.stop_hotkey_capture()
            else:
                # Programar otra verificación en 2 segundos
                self.auto_stop_timer = self.dialog.after(2000, self.auto_stop_capture)
    
    def stop_hotkey_capture(self):
        """Detiene la captura de teclas"""
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
            
        if hasattr(self, 'auto_stop_timer'):
            self.dialog.after_cancel(self.auto_stop_timer)
            
        self.listening_for_hotkey = False
        self.capture_btn.config(text="Capturar")
        
        # Limpiar conjuntos de teclas
        self.pressed_keys = set()
        
        # Si no hay combinación válida, restaurar el valor anterior
        current_hotkey = self.hotkey_var.get()
        if not current_hotkey or current_hotkey == "Presione una combinación de teclas...":
            self.hotkey_var.set(self.task_data.get('hotkey', ''))
    
    def format_hotkey(self, keys):
        """Formatea un conjunto de teclas en una cadena de hotkey"""
        if not keys:
            return ""
            
        # Ordenar las teclas: primero los modificadores, luego el resto
        sorted_keys = sorted(keys, key=lambda x: (
            0 if x in ['ctrl', 'alt', 'shift'] else 1,
            x
        ))
        return "+".join(sorted_keys)
    
    def on_key_press(self, key):
        """Maneja el evento de tecla presionada"""
        try:
            if not self.listening_for_hotkey:
                return False
                
            key_str = self.get_key_str(key)
            if not key_str:
                return True
            
            # Registrar tiempo y agregar tecla
            self.last_key_time = time.time()
            self.pressed_keys.add(key_str)
            
            # Actualizar la visualización
            self.update_hotkey_display()
            
            return True
            
        except Exception as e:
            print(f"Error en on_key_press: {e}")
            return False
    
    def on_key_release(self, key):
        """Maneja el evento de tecla liberada"""
        try:
            if not self.listening_for_hotkey:
                return False
                
            key_str = self.get_key_str(key)
            if not key_str:
                return True
            
            # Remover la tecla del conjunto de teclas presionadas
            if key_str in self.pressed_keys:
                self.pressed_keys.remove(key_str)
            
            # Si es una tecla no modificadora, marcar la combinación como completa
            if key_str not in ['ctrl', 'alt', 'shift']:
                self.combination_complete = True
            
            # Si ya no hay teclas presionadas y la combinación está completa
            if not self.pressed_keys and self.combination_complete:
                # Dejar un pequeño tiempo para asegurarnos de que todas las teclas se soltaron
                self.dialog.after(500, self.finalize_combination)
            
            return True
            
        except Exception as e:
            print(f"Error en on_key_release: {e}")
            return False
    
    def update_hotkey_display(self):
        """Actualiza la visualización del hotkey actual"""
        hotkey = self.format_hotkey(self.pressed_keys)
        self.hotkey_entry.config(state='normal')
        self.hotkey_var.set(hotkey)
        self.hotkey_entry.config(state='readonly')
    
    def finalize_combination(self):
        """Finaliza la captura de la combinación actual"""
        if not self.listening_for_hotkey:
            return
            
        try:
            # Convertir el conjunto de teclas en una combinación formateada
            hotkey = self.format_hotkey(self.pressed_keys)
            is_valid, error_msg = self.validate_hotkey(hotkey)
            
            if is_valid:
                # Guardar la combinación y detener la captura
                self.hotkey_entry.config(state='normal')
                self.hotkey_var.set(hotkey)
                self.hotkey_entry.config(state='readonly')
                
                # Programar la detención automática después de 2 segundos
                self.dialog.after(2000, self.stop_hotkey_capture)
            else:
                # Limpiar y continuar capturando
                self.pressed_keys.clear()
                self.combination_complete = False
                self.hotkey_entry.config(state='normal')
                self.hotkey_var.set("Presione una combinación de teclas...")
                self.hotkey_entry.config(state='readonly')
                messagebox.showwarning("Combinación inválida", error_msg)
                
        except Exception as e:
            print(f"Error al finalizar combinación: {e}")
            self.stop_hotkey_capture()
    
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
            hotkey = self.hotkey_var.get().strip()
            
            # Validaciones básicas
            if not all([name, process]):
                messagebox.showwarning("Error", "El nombre y el proceso son obligatorios")
                return
                
            # Validar hotkey
            is_valid, error_msg = self.validate_hotkey(hotkey)
            if not is_valid:
                messagebox.showwarning("Error", error_msg)
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
            
            # Validar archivo de sonido si está habilitado
            if self.custom_sound_var.get():
                sound_file = self.sound_file_var.get()
                if not sound_file or not os.path.exists(sound_file):
                    messagebox.showwarning("Error", "Debe seleccionar un archivo de sonido válido")
                    return
            
            # Crear resultado
            self.result = {
                'name': name,
                'process_name': process,
                'hotkey': hotkey,
                'target_affinity': target_affinity,
                'alerts': selected_alerts,
                'custom_sound': {
                    'enabled': self.custom_sound_var.get(),
                    'file': self.sound_file_var.get() if self.custom_sound_var.get() else None
                }
            }
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la tarea: {str(e)}")

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
            
        keys = set(hotkey.split("+"))
        
        # Debe tener al menos un modificador (ctrl, alt, shift)
        modifiers = {'ctrl', 'alt', 'shift'}
        if not any(mod in keys for mod in modifiers):
            return False, "La combinación debe incluir al menos una tecla modificadora (Ctrl, Alt, Shift)"
            
        # Debe tener al menos una tecla no modificadora
        if len(keys - modifiers) == 0:
            return False, "La combinación debe incluir al menos una tecla además de los modificadores"
        
        # No debe ser una combinación peligrosa o reservada
        dangerous_combinations = {
            {'ctrl', 'alt', 'delete'},
            {'ctrl', 'alt', 'supr'},
            {'ctrl', 'shift', 'escape'},
            {'win'},
            {'cmd'},
        }
        if any(dc.issubset(keys) for dc in dangerous_combinations):
            return False, "Combinación de teclas reservada del sistema"
            
        return True, ""

class TaskManager:
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
    
    def log_message(self, message: str, level: str = "info"):
        """Sistema de logging temporal hasta que la UI esté lista"""
        if hasattr(self.manager, 'log_text') and self.manager.log_text:
            # Si la UI está lista, usar su sistema de logging
            self.manager.log_message(message, level)
        else:
            # Si no, solo imprimir en consola
            prefix = {
                "error": "❌",
                "warning": "⚠️",
                "success": "✅",
                "info": "ℹ️"
            }.get(level, "ℹ️")
            print(f"{prefix} {message}")
    
    def log_message(self, message: str, level: str = "info"):
        """Sistema de logging temporal hasta que la UI esté lista"""
        if hasattr(self.manager, 'log_text') and self.manager.log_text:
            # Si la UI está lista, usar su sistema de logging
            self.manager.log_message(message, level)
        else:
            # Si no, solo imprimir en consola
            prefix = {
                "error": "❌",
                "warning": "⚠️",
                "success": "✅",
                "info": "ℹ️"
            }.get(level, "ℹ️")
            print(f"{prefix} {message}")
        
    def load_automated_tasks(self):
        """Carga las tareas automatizadas desde el archivo"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.automated_tasks = json.load(f)
                    
                # Configurar hotkeys para las tareas cargadas
                for task_id, task_data in self.automated_tasks.items():
                    self.setup_hotkey_listener(task_data['hotkey'], task_id)
                    
                self.manager.log_message("Tareas automatizadas cargadas correctamente", "success")
            else:
                self.manager.log_message("No se encontró archivo de tareas, se creará uno nuevo")
                self.save_automated_tasks()
        except Exception as e:
            self.manager.log_message(f"Error cargando tareas: {str(e)}", "error")
            self.automated_tasks = {}
            
    def save_automated_tasks(self):
        """Guarda las tareas automatizadas en el archivo"""
        try:
            # Crear backup del archivo existente
            if os.path.exists(self.tasks_file):
                backup_file = f"{self.tasks_file}.backup"
                try:
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(self.tasks_file, backup_file)
                except Exception as e:
                    self.manager.log_message(f"Error creando backup: {str(e)}", "warning")
            
            # Guardar nuevo archivo
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.automated_tasks, f, indent=4)
                
            self.manager.log_message("Tareas guardadas correctamente", "success")
        except Exception as e:
            self.manager.log_message(f"Error guardando tareas: {str(e)}", "error")

    def setup_hotkey_listener(self, hotkey: str, task_id: str):
        """Configura un listener para una combinación de teclas usando pynput"""
        try:
            # Remover listener anterior si existe
            if hotkey in self.hotkey_listeners:
                self.remove_hotkey_listener(hotkey)
            
            # Convertir el hotkey string a una lista de teclas
            keys = hotkey.lower().split('+')
            required_keys = set(keys)
            
            # Clase para manejar el estado de las teclas
            class HotkeyState:
                def __init__(self):
                    self.pressed_keys = set()
                    self.suppress_next = False
            
            state = HotkeyState()
            
            def on_press(key):
                try:
                    # Convertir la tecla a string
                    if hasattr(key, 'char'):
                        key_str = key.char.lower()
                    else:
                        key_str = str(key).replace('Key.', '').lower()
                    
                    # Agregar la tecla al conjunto de teclas presionadas
                    state.pressed_keys.add(key_str)
                    
                    # Verificar si todas las teclas requeridas están presionadas
                    if required_keys.issubset(state.pressed_keys) and not state.suppress_next:
                        state.suppress_next = True  # Evitar activaciones múltiples
                        # Ejecutar la tarea en el hilo principal
                        self.manager.root.after(0, lambda: self.execute_automated_task(task_id))
                except:
                    pass
            
            def on_release(key):
                try:
                    # Convertir la tecla a string
                    if hasattr(key, 'char'):
                        key_str = key.char.lower()
                    else:
                        key_str = str(key).replace('Key.', '').lower()
                    
                    # Remover la tecla del conjunto de teclas presionadas
                    state.pressed_keys.discard(key_str)
                    
                    # Si todas las teclas fueron liberadas, permitir nueva activación
                    if not state.pressed_keys:
                        state.suppress_next = False
                except:
                    pass
            
            # Crear y guardar el listener
            listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            self.hotkey_listeners[hotkey] = {
                'listener': listener,
                'task_id': task_id
            }
            
            self.manager.log_message(f"Hotkey global configurado: {hotkey}", "success")
            
        except Exception as e:
            self.manager.log_message(f"Error configurando hotkey {hotkey}: {str(e)}", "error")
            
    def remove_hotkey_listener(self, hotkey: str):
        """Elimina un listener de hotkey"""
        try:
            if hotkey in self.hotkey_listeners:
                self.hotkey_listeners[hotkey]['listener'].stop()
                del self.hotkey_listeners[hotkey]
        except Exception as e:
            self.manager.log_message(f"Error removiendo hotkey {hotkey}: {str(e)}", "error")
            
    def execute_automated_task(self, task_id: str):
        """Ejecuta una tarea automatizada"""
        if task_id not in self.automated_tasks:
            return
            
        task_data = self.automated_tasks[task_id]
        
        try:
            # Buscar proceso por nombre
            target_process = None
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == task_data['process_name'].lower():
                    target_process = proc
                    break
                    
            if not target_process:
                self.manager.log_message(f"Proceso no encontrado: {task_data['process_name']}", "warning")
                return
                
            # Aplicar la afinidad configurada
            target_affinity = task_data.get('target_affinity', [0])  # Por defecto CPU0
            target_process.cpu_affinity(target_affinity)
            affinity_str = ', '.join([f"CPU{cpu}" for cpu in target_affinity])
            
            self.manager.log_message(
                f"Tarea ejecutada: {task_data['name']} - {task_data['process_name']} "
                f"→ CPUs asignadas: {affinity_str}", 
                "success"
            )
            
            # Mostrar notificación
            self.manager._last_process_name = task_data['process_name']
            
            # Manejar cada tipo de alerta seleccionado
            alerts = task_data.get('alerts', ['notification', 'sound'])  # Por compatibilidad
            message = f"Afinidad aplicada a {task_data['process_name']}"
            
            if 'notification' in alerts:
                self.manager.show_notification(message)
            
            if 'sound' in alerts:
                # Verificar si hay sonido personalizado
                if task_data.get('custom_sound', {}).get('enabled', False):
                    sound_file = task_data['custom_sound']['file']
                    if sound_file and os.path.exists(sound_file):
                        try:
                            if sound_file.lower().endswith('.mp3'):
                                pygame.mixer.music.load(sound_file)
                                pygame.mixer.music.play()
                            else:
                                sound = pygame.mixer.Sound(sound_file)
                                sound.play()
                        except Exception as e:
                            self.manager.log_message(f"Error reproduciendo sonido: {str(e)}", "error")
                            winsound.MessageBeep()  # Sonido por defecto como respaldo
                    else:
                        winsound.MessageBeep()
                else:
                    winsound.MessageBeep()
            
            if 'tray' in alerts:
                # Mostrar icono en la bandeja del sistema
                try:
                    import win32gui
                    import win32con
                    hwnd = win32gui.FindWindow(None, "Administrador de Afinidad de Procesos")
                    if hwnd:
                        win32gui.Shell_NotifyIcon(win32con.NIM_MODIFY, 
                            (hwnd, 0, win32con.NIF_INFO, win32con.WM_USER+20,
                            0, "Afinidad Cambiada", message, 200, "Administrador de Afinidad"))
                except:
                    pass  # Si falla, ignoramos silenciosamente
            
            if 'flash' in alerts:
                # Hacer parpadear la ventana
                try:
                    import win32gui
                    import win32con
                    hwnd = win32gui.FindWindow(None, "Administrador de Afinidad de Procesos")
                    if hwnd and not win32gui.IsWindowVisible(hwnd):
                        win32gui.FlashWindow(hwnd, True)
                except:
                    pass  # Si falla, ignoramos silenciosamente
            
            self.manager.log_message(
                f"Tarea ejecutada: {task_data['name']} - Alertas: {', '.join(alerts)}", 
                "success"
            )
            
        except psutil.AccessDenied:
            self.manager.log_message(f"Acceso denegado: {task_data['name']}", "error")
        except Exception as e:
            self.manager.log_message(f"Error en tarea {task_data['name']}: {str(e)}", "error")

    def add_task(self, task_data: Dict[str, Any]) -> str:
        """Agrega una nueva tarea automatizada"""
        try:
            task_id = str(uuid.uuid4())
            
            # Asegurar que los datos son serializables
            serializable_data = {
                'name': str(task_data.get('name', '')),
                'process_name': str(task_data.get('process_name', '')),
                'hotkey': str(task_data.get('hotkey', '')),
                'target_affinity': list(task_data.get('target_affinity', [])),
                'alerts': list(task_data.get('alerts', ['notification', 'sound'])),
                'custom_sound': {
                    'enabled': bool(task_data.get('custom_sound', {}).get('enabled', False)),
                    'file': str(task_data.get('custom_sound', {}).get('file', '')) or None
                }
            }
            
            self.automated_tasks[task_id] = serializable_data
            
            # Configurar hotkey
            self.setup_hotkey_listener(task_data['hotkey'], task_id)
            
            # Guardar cambios
            self.save_automated_tasks()
            self.manager.log_message(
                f"Tarea creada: {task_data['name']} - Hotkey: {task_data['hotkey']}", 
                "success"
            )
            
            return task_id
            
        except Exception as e:
            self.manager.log_message(f"Error al crear la tarea: {str(e)}", "error")
            raise

    def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea automatizada"""
        try:
            if not task_id:
                messagebox.showwarning("Advertencia", "Por favor, seleccione una tarea para eliminar")
                return False
                
            if task_id not in self.automated_tasks:
                messagebox.showerror("Error", "Tarea no encontrada")
                return False
            
            # Pedir confirmación
            task_name = self.automated_tasks[task_id]['name']
            if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la tarea '{task_name}'?"):
                return False
                
            task_data = self.automated_tasks[task_id]
            hotkey = task_data.get('hotkey')
            
            if hotkey:
                self.remove_hotkey_listener(hotkey)
                
            del self.automated_tasks[task_id]
            self.save_automated_tasks()
            
            # Actualizar la vista
            self.manager.ui.refresh_tasks_display(self.manager)
            self.manager.log_message(f"Tarea eliminada: {task_name}", "success")
            
            return True
            
        except Exception as e:
            self.manager.log_message(f"Error eliminando tarea: {str(e)}", "error")
            messagebox.showerror("Error", f"Error al eliminar la tarea: {str(e)}")
            return False

    def edit_task(self, task_id: str, new_task_data: Dict[str, Any]) -> bool:
        """Edita una tarea existente"""
        try:
            if task_id not in self.automated_tasks:
                messagebox.showerror("Error", "La tarea no existe")
                return False
                
            old_task = self.automated_tasks[task_id]
            old_hotkey = old_task.get('hotkey')
            
            # Remover el listener anterior
            if old_hotkey:
                self.remove_hotkey_listener(old_hotkey)
            
            # Actualizar la tarea
            self.automated_tasks[task_id] = new_task_data
            
            # Configurar el nuevo hotkey
            new_hotkey = new_task_data.get('hotkey')
            if new_hotkey:
                self.setup_hotkey_listener(new_hotkey, task_id)
            
            # Guardar los cambios
            self.save_automated_tasks()
            
            # Actualizar la vista
            self.manager.ui.refresh_tasks_display(self.manager)
            
            # Mostrar mensaje de éxito
            self.manager.log_message(f"Tarea editada: {new_task_data['name']}", "success")
            messagebox.showinfo("Éxito", f"La tarea '{new_task_data['name']}' ha sido actualizada")
            
            return True
            
        except Exception as e:
            error_msg = f"Error editando tarea: {str(e)}"
            self.manager.log_message(error_msg, "error")
            messagebox.showerror("Error", error_msg)
            return False

    def show_notification_for_task(self, task_data: Dict[str, Any], mode: str):
        """Muestra una notificación para una tarea"""
        try:
            alert_type = task_data.get('alert_type', 'combinado')
            custom_config = task_data.get('custom_notification')
            
            if custom_config:
                # Usar configuración personalizada
                message = custom_config.get(f'message_{mode}', 
                    "🚀 Afinidad ALTA aplicada" if mode == "high" else "💚 Afinidad BAJA aplicada")
                
                if custom_config.get('show_process_name', True):
                    message = f"{message} - {task_data['process_name']}"
                
                if custom_config.get('sound_enabled', True):
                    sound_file = custom_config.get('sound_file')
                    if sound_file and os.path.exists(sound_file):
                        self.play_notification_sound_custom(custom_config)
                    else:
                        winsound.MessageBeep()
                
                self.manager.show_notification(message, mode)
            else:
                # Usar configuración global
                message = (self.manager.notification_config['message_high'] 
                         if mode == "high" 
                         else self.manager.notification_config['message_low'])
                
                if self.manager.notification_config['show_process_name']:
                    message = f"{message} - {task_data['process_name']}"
                    
                self.manager.show_notification(message, mode)
        
        except Exception as e:
            self.manager.log_message(f"Error en notificación: {str(e)}", "error")
    
    def edit_task_dialog(self, task_id: str):
        """Muestra el diálogo para editar una tarea"""
        if not task_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una tarea para editar")
            return
            
        if task_id not in self.automated_tasks:
            messagebox.showerror("Error", "Tarea no encontrada")
            return
            
        task_data = self.automated_tasks[task_id].copy()
        dialog = TaskDialog(self.manager.root, task_data, is_edit=True)
        self.manager.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if self.edit_task(task_id, dialog.result):
                self.manager.ui.refresh_tasks_display(self.manager)
                self.manager.log_message(f"Tarea editada: {dialog.result['name']}", "success")
            else:
                messagebox.showerror("Error", "No se pudo editar la tarea")
                self.manager.log_message("Error al editar la tarea", "error")
