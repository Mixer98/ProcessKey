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
        self.setup_hotkey_service_tab(manager)  # Nueva pestaña de servicio de hotkeys

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
        
        # También actualizar la pestaña de hotkeys si está disponible
        if hasattr(manager, 'refresh_hotkeys_display'):
            manager.refresh_hotkeys_display()

    def setup_hotkey_service_tab(self, manager):
        """Configura la pestaña de administración del servicio de hotkeys"""
        hotkey_frame = ttk.Frame(manager.notebook)
        manager.notebook.add(hotkey_frame, text="⌨️ Servicio de Hotkeys")
        
        # Configurar el frame principal para el scrolling
        hotkey_frame.columnconfigure(0, weight=1)
        hotkey_frame.rowconfigure(0, weight=1)
        
        # Crear canvas y scrollbar para el contenido scrolleable
        canvas = tk.Canvas(hotkey_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(hotkey_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configurar el scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Colocar canvas y scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configurar el frame scrolleable
        scrollable_frame.columnconfigure(0, weight=1)
        
        # Funciones para el scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Ahora todo el contenido va en scrollable_frame en lugar de hotkey_frame
        
        # Frame superior - Estado del servicio y controles generales
        service_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Estado del Servicio", padding="15")
        service_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15), padx=10)
        service_frame.columnconfigure(0, weight=1)
        
        # Estado actual del servicio
        status_frame = ttk.Frame(service_frame)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Estado del Servicio:", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        manager.service_status_label = ttk.Label(status_frame, text="🟢 Funcionando", 
                                               foreground='green', font=('Arial', 12, 'bold'))
        manager.service_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Información del servicio
        info_frame = ttk.Frame(service_frame)
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)
        
        # Labels informativos
        info_labels = [
            ("Hotkeys Activos:", "active_hotkeys_label", "0"),
            ("Última Activación:", "last_activation_label", "Ninguna"),
            ("Errores de Captura:", "capture_errors_label", "0"),
        ]
        
        for row, (text, attr, default) in enumerate(info_labels):
            ttk.Label(info_frame, text=text, font=('Arial', 10, 'bold')).grid(
                row=row, column=0, sticky=tk.W, pady=2)
            label = ttk.Label(info_frame, text=default, font=('Arial', 10))
            label.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            setattr(manager, attr, label)
        
        # Botones de control del servicio
        buttons_frame = ttk.Frame(service_frame)
        buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(buttons_frame, text="🔄 Reiniciar Servicio", 
                  command=lambda: manager.restart_hotkey_service()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame, text="⚠️ Detener Servicio", 
                  command=lambda: manager.stop_hotkey_service()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame, text="▶️ Iniciar Servicio", 
                  command=lambda: manager.start_hotkey_service()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons_frame, text="🧪 Probar Captura", 
                  command=lambda: manager.test_hotkey_capture()).pack(side=tk.LEFT)
        
        # Frame central - Lista de hotkeys activos
        hotkeys_frame = ttk.LabelFrame(scrollable_frame, text="📋 Hotkeys Registrados", padding="8")
        hotkeys_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15), padx=10)
        hotkeys_frame.columnconfigure(0, weight=1)
        hotkeys_frame.rowconfigure(0, weight=1)
        
        # Treeview para mostrar hotkeys activos
        hotkey_columns = ('Combinación', 'Tarea', 'Proceso', 'Estado', 'Última Activación', 'Contador')
        manager.hotkeys_tree = ttk.Treeview(hotkeys_frame, columns=hotkey_columns, show='headings', height=10)
        
        # Configurar columnas
        manager.hotkeys_tree.heading('Combinación', text='⌨️ Combinación de Teclas')
        manager.hotkeys_tree.heading('Tarea', text='📝 Tarea Asociada')
        manager.hotkeys_tree.heading('Proceso', text='🎯 Proceso Objetivo')
        manager.hotkeys_tree.heading('Estado', text='📊 Estado')
        manager.hotkeys_tree.heading('Última Activación', text='🕒 Última Activación')
        manager.hotkeys_tree.heading('Contador', text='🔢 Veces Usado')
        
        # Anchos de columnas
        manager.hotkeys_tree.column('Combinación', width=120, minwidth=100)
        manager.hotkeys_tree.column('Tarea', width=150, minwidth=120)
        manager.hotkeys_tree.column('Proceso', width=120, minwidth=100)
        manager.hotkeys_tree.column('Estado', width=100, minwidth=80)
        manager.hotkeys_tree.column('Última Activación', width=120, minwidth=100)
        manager.hotkeys_tree.column('Contador', width=80, minwidth=60)
        
        manager.hotkeys_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para hotkeys
        hotkey_scrollbar = ttk.Scrollbar(hotkeys_frame, orient=tk.VERTICAL, command=manager.hotkeys_tree.yview)
        hotkey_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        manager.hotkeys_tree.configure(yscrollcommand=hotkey_scrollbar.set)
        
        # Frame inferior - Configuración avanzada
        config_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Configuración Avanzada", padding="10")
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15), padx=10)
        config_frame.columnconfigure(1, weight=1)
        
        # Configuraciones del servicio
        ttk.Label(config_frame, text="Tiempo de espera entre capturas (ms):", 
                 font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        manager.capture_delay_var = tk.StringVar(value="100")
        ttk.Entry(config_frame, textvariable=manager.capture_delay_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(config_frame, text="Modo de depuración:", 
                 font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        manager.debug_mode_var = tk.BooleanVar()
        ttk.Checkbutton(config_frame, text="Mostrar información detallada", 
                       variable=manager.debug_mode_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Botones de configuración
        config_buttons_frame = ttk.Frame(config_frame)
        config_buttons_frame.grid(row=2, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(config_buttons_frame, text="💾 Guardar Configuración", 
                  command=lambda: manager.save_hotkey_config()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(config_buttons_frame, text="🔄 Cargar Configuración", 
                  command=lambda: manager.load_hotkey_config()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(config_buttons_frame, text="🏭 Restaurar Por Defecto", 
                  command=lambda: manager.reset_hotkey_config()).pack(side=tk.LEFT)

        # Nueva sección: Sistema de Monitoreo y Recuperación Automática
        monitoring_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Sistema de Monitoreo y Recuperación", padding="15")
        monitoring_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15), padx=10)
        monitoring_frame.columnconfigure(1, weight=1)
        
        # Estado de salud del sistema
        health_frame = ttk.Frame(monitoring_frame)
        health_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        health_frame.columnconfigure(1, weight=1)
        
        ttk.Label(health_frame, text="Estado de Salud:", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        manager.health_status_label = ttk.Label(health_frame, text="⚪ Inicializando...", 
                                              font=('Arial', 12, 'bold'))
        manager.health_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Información de monitoreo
        monitor_info_frame = ttk.Frame(monitoring_frame)
        monitor_info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        monitor_info_frame.columnconfigure(1, weight=1)
        
        # Labels informativos del monitoreo
        monitor_labels = [
            ("Tiempo sin Captura:", "last_capture_label", "0s"),
            ("Intentos de Recuperación:", "recovery_attempts_label", "0"),
            ("Última Recuperación:", "last_recovery_label", "Nunca"),
        ]
        
        for row, (text, attr, default) in enumerate(monitor_labels):
            ttk.Label(monitor_info_frame, text=text, font=('Arial', 10, 'bold')).grid(
                row=row, column=0, sticky=tk.W, pady=3)
            label = ttk.Label(monitor_info_frame, text=default, font=('Arial', 10))
            label.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)
            setattr(manager, attr, label)
        
        # Configuración del monitoreo
        monitor_config_frame = ttk.Frame(monitoring_frame)
        monitor_config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        monitor_config_frame.columnconfigure(1, weight=1)
        
        # Timeout de monitoreo
        ttk.Label(monitor_config_frame, text="Timeout de Monitoreo (minutos):", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        manager.timeout_var = tk.StringVar(value="5")
        timeout_entry = ttk.Entry(monitor_config_frame, textvariable=manager.timeout_var, width=10)
        timeout_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        timeout_entry.bind('<Return>', lambda e: manager.set_monitoring_timeout())
        
        # Recuperación automática
        ttk.Label(monitor_config_frame, text="Recuperación Automática:", 
                 font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        manager.auto_recovery_var = tk.BooleanVar(value=True)
        recovery_check = ttk.Checkbutton(monitor_config_frame, text="Activar recuperación automática", 
                                       variable=manager.auto_recovery_var,
                                       command=manager.toggle_auto_recovery)
        recovery_check.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Botones de control del monitoreo
        monitor_buttons_frame = ttk.Frame(monitoring_frame)
        monitor_buttons_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(monitor_buttons_frame, text="🔧 Prueba Manual", 
                  command=lambda: manager.manual_recovery_test()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(monitor_buttons_frame, text="🔄 Reset Contador", 
                  command=lambda: manager.reset_recovery_counter()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(monitor_buttons_frame, text="⚡ Aplicar Timeout", 
                  command=lambda: manager.set_monitoring_timeout()).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(monitor_buttons_frame, text="📊 Ver Estado", 
                  command=lambda: manager._update_monitoring_ui()).pack(side=tk.LEFT)
        
        # Agregar un poco de espacio al final para mejor apariencia
        ttk.Label(scrollable_frame, text="").grid(row=4, column=0, pady=20)
