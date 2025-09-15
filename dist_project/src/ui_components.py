"""
Componentes de la interfaz de usuario para el Administrador de Afinidad
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import time

class UIComponents:
    def setup_ui(self, manager):
        """Configura la interfaz de usuario principal"""
        # Configurar la interfaz
        self._setup_ui_components(manager)
        
        # Notificar que la UI está lista
        if hasattr(manager, 'task_manager'):
            manager.task_manager.ui_ready = True
    
    def _setup_ui_components(self, manager):
        """Configuración interna de los componentes de la UI"""
        # Frame principal
        main_frame = ttk.Frame(manager.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar peso de las filas y columnas
        manager.root.columnconfigure(0, weight=1)
        manager.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3, minsize=800)
        main_frame.columnconfigure(1, weight=1, minsize=350)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🖥️ Administrador de Afinidad de Procesos", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # Advertencia de permisos
        if not manager.is_admin:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.grid(row=0, column=0, columnspan=2, pady=(35, 15), sticky=(tk.W, tk.E))
            
            warning_label = ttk.Label(warning_frame, 
                                    text="⚠️ Ejecute como administrador para modificar la afinidad de todos los procesos",
                                    foreground='red', font=('Arial', 10, 'bold'))
            warning_label.pack()
        
        # Crear notebook
        manager.notebook = ttk.Notebook(main_frame)
        manager.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))

        # Frame log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Registro de Actividad", padding="8")
        log_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # Frame de botones del log
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Botones de control del log
        ttk.Button(log_buttons_frame, text="🗑️ Limpiar Log", 
                  command=lambda: manager.clear_log()).pack(side=tk.LEFT, padx=(0, 5))
        
        # Variable para controlar visibilidad del log
        manager.log_visible = tk.BooleanVar(value=True)
        manager.toggle_log_btn = ttk.Button(log_buttons_frame, text="👁️ Ocultar Log", 
                                          command=lambda: manager.toggle_log_visibility())
        manager.toggle_log_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Botón para minimizar a la bandeja
        ttk.Button(log_buttons_frame, text="📌 A Bandeja", 
                  command=lambda: manager.smart_minimize()).pack(side=tk.LEFT)
        
        # Log de actividad
        manager.log_text = scrolledtext.ScrolledText(log_frame, height=25, state='disabled', 
                                                 width=45, font=('Consolas', 9))
        manager.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar pestañas
        self.setup_manual_control_tab(manager)
        self.setup_tasks_tab(manager)  # Nueva pestaña de tareas

    def setup_manual_control_tab(self, manager):
        """Configura la pestaña de control manual"""
        manual_frame = ttk.Frame(manager.notebook)
        manager.notebook.add(manual_frame, text="🎯 Control Manual")
        
        manual_frame.columnconfigure(0, weight=2, minsize=500)
        manual_frame.columnconfigure(1, weight=1, minsize=350)
        manual_frame.rowconfigure(0, weight=1)
        
        # Frame lista de procesos
        left_frame = ttk.LabelFrame(manual_frame, text="📋 Procesos en Ejecución", padding="8")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # Setup de los componentes de control de procesos
        self.setup_process_controls(manager, left_frame)
        
        # Setup del frame derecho de control de afinidad
        self.setup_affinity_control_frame(manager, manual_frame)

    def setup_process_controls(self, manager, parent_frame):
        """Configura los controles de procesos"""
        process_controls_frame = ttk.Frame(parent_frame)
        process_controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        process_controls_frame.columnconfigure(0, weight=1)
        
        # Barra de búsqueda
        search_frame = ttk.Frame(process_controls_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        manager.search_var = tk.StringVar()
        manager.search_entry = ttk.Entry(search_frame, textvariable=manager.search_var, width=30)
        manager.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        manager.search_entry.bind('<KeyRelease>', manager.on_search_change)
        
        ttk.Button(search_frame, text="Limpiar", command=manager.clear_search).grid(row=0, column=2)
        
        # Botón de actualizar
        ttk.Button(process_controls_frame, text="Actualizar Lista", 
                  command=manager.refresh_process_list).grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Treeview de procesos
        columns = ('PID', 'Nombre', 'CPU%', 'Memoria')
        manager.process_tree = ttk.Treeview(parent_frame, columns=columns, show='headings', height=25)
        
        for col, width in zip(columns, [90, 300, 90, 120]):
            manager.process_tree.heading(col, text=col)
            manager.process_tree.column(col, width=width, minwidth=70)
        
        manager.process_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        manager.process_tree.bind('<<TreeviewSelect>>', manager.on_process_select)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=manager.process_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        manager.process_tree.configure(yscrollcommand=scrollbar.set)

    def setup_affinity_control_frame(self, manager, parent_frame):
        """Configura el frame de control de afinidad"""
        right_frame = ttk.LabelFrame(parent_frame, text="⚙️ Control de Afinidad de CPU", padding="8")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(2, weight=1)
        right_frame.columnconfigure(0, weight=1)
        
        # Información del proceso
        info_frame = ttk.LabelFrame(right_frame, text="📊 Información del Proceso", padding="8")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)
        
        # Labels de información
        labels = [
            ("Proceso Seleccionado:", "selected_process_label", "Ninguno"),
            ("PID:", "pid_label", "-"),
            ("Afinidad Actual:", "current_affinity_label", "-")
        ]
        
        for row, (text, attr, default) in enumerate(labels):
            ttk.Label(info_frame, text=text, font=('Arial', 9, 'bold')).grid(
                row=row, column=0, sticky=tk.W, pady=3)
            label = ttk.Label(info_frame, text=default, font=('Arial', 10))
            label.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)
            setattr(manager, attr, label)
        
        manager.selected_process_label.configure(foreground='blue')
        
        # Frame de selección de CPUs
        cpu_frame = ttk.LabelFrame(right_frame, 
                                  text=f"🔧 Seleccionar CPUs ({manager.cpu_count} disponibles)", 
                                  padding="10")
        cpu_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Checkboxes de CPUs
        manager.cpu_vars = []
        manager.cpu_checkboxes = []
        cols = min(6, max(2, manager.cpu_count // 2))
        
        for i in range(manager.cpu_count):
            var = tk.BooleanVar()
            manager.cpu_vars.append(var)
            
            checkbox = ttk.Checkbutton(cpu_frame, text=f"CPU {i}", variable=var)
            row = i // cols
            col = i % cols
            checkbox.grid(row=row, column=col, sticky=tk.W, padx=8, pady=5)
            manager.cpu_checkboxes.append(checkbox)
        
        # Botones de control
        cpu_button_frame = ttk.Frame(right_frame)
        cpu_button_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        cpu_button_frame.columnconfigure(0, weight=1)
        cpu_button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(cpu_button_frame, text="✅ Seleccionar Todas", 
                  command=manager.select_all_cpus).grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(cpu_button_frame, text="❌ Deseleccionar Todas", 
                  command=manager.deselect_all_cpus).grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Botones principales
        manager.apply_btn = ttk.Button(right_frame, text="🚀 Aplicar Afinidad", 
                                      command=manager.apply_affinity, state='disabled',
                                      style='Accent.TButton')
        manager.apply_btn.grid(row=4, column=0, pady=(15, 8), sticky=(tk.W, tk.E))
        
        manager.create_task_btn = ttk.Button(right_frame, text="🔧 Crear Tarea Automatizada", 
                                            command=manager.show_create_task_dialog, state='disabled')
        manager.create_task_btn.grid(row=5, column=0, pady=(0, 10), sticky=(tk.W, tk.E))

    def setup_tasks_tab(self, manager):
        """Configura la pestaña de tareas automatizadas"""
        tasks_frame = ttk.Frame(manager.notebook)
        manager.notebook.add(tasks_frame, text="⚡ Tareas Automatizadas")
        
        tasks_frame.columnconfigure(0, weight=1)
        tasks_frame.rowconfigure(1, weight=1)
        
        # Frame superior - Controles
        control_frame = ttk.LabelFrame(tasks_frame, text="🎛️ Controles de Tareas", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Primera fila de botones
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(buttons_frame, text="✏️ Editar Tarea", 
                  command=lambda: manager.task_manager.edit_task_dialog(
                      manager.tasks_tree.selection()[0] if manager.tasks_tree.selection() else None
                  )).pack(side=tk.LEFT, padx=(0, 8))
                  
        ttk.Button(buttons_frame, text="🗑️ Eliminar Tarea",
                  command=lambda: manager.task_manager.delete_task_with_confirmation(
                      manager.tasks_tree.selection()[0] if manager.tasks_tree.selection() else None
                  )).pack(side=tk.LEFT, padx=(0, 8))
                  
        ttk.Button(buttons_frame, text="🧪 Probar Tarea",
                  command=lambda: manager.task_manager.execute_automated_task(
                      manager.tasks_tree.selection()[0] if manager.tasks_tree.selection() else None
                  )).pack(side=tk.LEFT)
        
        # Estado del sistema
        status_frame = ttk.Frame(control_frame)
        status_frame.grid(row=1, column=0, pady=8, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="🔘 Estado del Sistema:", 
                 font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        manager.keyboard_status_label = ttk.Label(status_frame, text="Iniciado", 
                                                foreground='green', font=('Arial', 9, 'bold'))
        manager.keyboard_status_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # Información sobre hotkeys
        info_label = ttk.Label(control_frame, 
                              text="💡 Los hotkeys funcionan globalmente (incluso en pantalla completa)", 
                              font=('Arial', 9, 'bold'), foreground='blue')
        info_label.grid(row=2, column=0, pady=(5, 0))
        
        # Frame central - Lista de tareas
        list_frame = ttk.LabelFrame(tasks_frame, text="📋 Tareas Configuradas", padding="8")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview para mostrar tareas
        columns = ('Nombre', 'Proceso', 'Hotkey', 'CPUs', 'Estado', 'Alertas', 'Info')
        manager.tasks_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        # Configurar columnas
        manager.tasks_tree.heading('Nombre', text='📝 Nombre de la Tarea')
        manager.tasks_tree.heading('Proceso', text='🎯 Proceso Objetivo')
        manager.tasks_tree.heading('Hotkey', text='⌨️ Tecla Rápida')
        manager.tasks_tree.heading('CPUs', text='💻 CPUs Asignadas')
        manager.tasks_tree.heading('Estado', text='📊 Estado')
        manager.tasks_tree.heading('Alertas', text='🔔 Alertas')
        manager.tasks_tree.heading('Info', text='ℹ️ Info')
        
        # Anchos de columnas
        manager.tasks_tree.column('Nombre', width=180, minwidth=120)
        manager.tasks_tree.column('Proceso', width=140, minwidth=100)
        manager.tasks_tree.column('Hotkey', width=140, minwidth=100)
        manager.tasks_tree.column('CPUs', width=150, minwidth=100)
        manager.tasks_tree.column('Estado', width=100, minwidth=80)
        manager.tasks_tree.column('Alertas', width=150, minwidth=100)
        manager.tasks_tree.column('Info', width=100, minwidth=60)
        
        manager.tasks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=manager.tasks_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        manager.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        # Las tareas se cargarán después de que el TaskManager esté listo

    def refresh_tasks_display(self, manager):
        """Actualiza la visualización de tareas en el treeview"""
        if not hasattr(manager, 'task_manager') or not manager.task_manager:
            return
            
        # Limpiar treeview
        for item in manager.tasks_tree.get_children():
            manager.tasks_tree.delete(item)
        
        # Agregar tareas cargadas
        for task_id, task_data in manager.task_manager.automated_tasks.items():
            # Obtener la afinidad configurada
            cpu_str = ', '.join([f"CPU{cpu}" for cpu in task_data.get('target_affinity', [])])
            
            # Obtener los tipos de alerta seleccionados
            alerts = task_data.get('alerts', ['notification', 'sound'])
            alert_types = {
                'notification': 'Notificación',
                'sound': 'Sonido',
                'tray': 'Bandeja',
                'flash': 'Parpadeo'
            }
            alert_str = ', '.join([alert_types.get(a, a) for a in alerts])
            
            # Insertar en el treeview
            manager.tasks_tree.insert('', 'end', iid=task_id, values=(
                task_data['name'],
                task_data['process_name'],
                task_data['hotkey'],
                cpu_str,
                "✅ Activada",  # Estado de la tarea
                alert_str,  # Tipos de alerta configurados
                ""  # Columna extra para futura información
            ))
