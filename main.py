#!/usr/bin/env python3
"""
Python App Launcher - Creates activation scripts for each app
Uses xterm for terminal execution
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, colorchooser
import subprocess
import os
import sys
import json
import shutil
from datetime import datetime
import platform
import threading
from icon_generator import IconGenerator

class PythonAppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Python App Launcher")
        self.root.geometry("1000x700")
        
        # Configuration
        self.config_dir = os.path.join(os.path.expanduser("~"), ".python_app_launcher")
        self.scripts_dir = os.path.join(self.config_dir, "scripts")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        self.apps_file = os.path.join(self.config_dir, "apps.json")
        self.saved_apps = []
        
        # Variables
        self.venv_path_var = tk.StringVar()
        self.script_path_var = tk.StringVar()
        self.args_var = tk.StringVar()
        self.workdir_var = tk.StringVar(value=os.getcwd())
        self.app_name_var = tk.StringVar()
        
        # Create GUI
        self.create_gui()
        
        # Load saved apps
        self.load_apps()
        
        # Bind keyboard shortcuts
        self.setup_shortcuts()
    
    def create_gui(self):
        """Create the GUI layout"""
        # Main container with notebook (tabs)
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: App Launcher
        launcher_tab = ttk.Frame(self.notebook)
        self.notebook.add(launcher_tab, text="App Launcher")
        
        launcher_container = ttk.Frame(launcher_tab, padding="10")
        launcher_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        left_panel = ttk.LabelFrame(launcher_container, text="App Configuration", padding="15")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_controls_panel(left_panel)
        
        # Right panel - Apps list and output
        right_panel = ttk.Frame(launcher_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Apps list
        apps_frame = ttk.LabelFrame(right_panel, text="Saved Applications", padding="10")
        apps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.create_apps_list(apps_frame)
        
        # Output console
        output_frame = ttk.LabelFrame(right_panel, text="Console Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_output_console(output_frame)
        
        # Tab 2: Desktop File Manager
        desktop_tab = ttk.Frame(self.notebook)
        self.notebook.add(desktop_tab, text="Desktop Files")
        
        self.create_desktop_files_tab(desktop_tab)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_desktop_files_tab(self, parent):
        """Create the Desktop Files tab for generating .desktop files"""
        container = ttk.Frame(parent, padding="15")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            container,
            text="Generate Ubuntu Desktop Files",
            font=("Arial", 14, "bold")
        )
        title.pack(pady=(0, 20))
        
        # Info box
        info_text = ("Desktop files allow your Python apps to appear in the Ubuntu Applications menu.\n"
                     "They will be saved to ~/.local/share/applications/ and sync with your system.")
        info_label = ttk.Label(container, text=info_text, justify=tk.LEFT, foreground="#666666")
        info_label.pack(pady=(0, 15))
        
        # Apps list frame
        list_frame = ttk.LabelFrame(container, text="Saved Applications", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Treeview for desktop file management
        columns = ("name", "status", "created")
        self.desktop_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.desktop_tree.heading("name", text="Application Name")
        self.desktop_tree.heading("status", text="Desktop File Status")
        self.desktop_tree.heading("created", text="Created")
        
        self.desktop_tree.column("name", width=150)
        self.desktop_tree.column("status", width=200)
        self.desktop_tree.column("created", width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.desktop_tree.yview)
        self.desktop_tree.configure(yscrollcommand=scrollbar.set)
        
        self.desktop_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        button_frame = ttk.LabelFrame(container, text="Actions", padding="10")
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(
            button_frame,
            text="📋 Generate Selected",
            command=self.generate_selected_desktop_file,
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="🚀 Generate & Refresh Apps",
            command=self.generate_and_refresh_desktop,
            width=23
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="📁 Open Desktop Files Folder",
            command=self.open_desktop_files_folder,
            width=22
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="🗑 Delete Desktop File",
            command=self.delete_desktop_file,
            width=18
        ).pack(side=tk.LEFT)
        
        # Options frame
        options_frame = ttk.LabelFrame(container, text="Desktop File & Icon Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Icon generation type selection
        icon_type_frame = ttk.Frame(options_frame)
        icon_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(icon_type_frame, text="Icon Type:", width=20).pack(side=tk.LEFT, padx=(0, 5))
        self.icon_type_var = tk.StringVar(value="generate")
        ttk.Combobox(icon_type_frame, textvariable=self.icon_type_var, 
                    values=["generate", "custom", "system"], state="readonly", width=15).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(icon_type_frame, text="(Generate: auto, Custom: upload, System: name)", 
                 foreground="#666666", font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Generated icon options (shown when generate is selected)
        gen_icon_frame = ttk.LabelFrame(options_frame, text="Generated Icon Settings", padding="10")
        gen_icon_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Background color
        bg_color_frame = ttk.Frame(gen_icon_frame)
        bg_color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(bg_color_frame, text="Background Color:", width=20).pack(side=tk.LEFT, padx=(0, 5))
        self.bg_color_var = tk.StringVar(value="#4285F4")
        bg_color_entry = ttk.Entry(bg_color_frame, textvariable=self.bg_color_var, width=15)
        bg_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        def pick_bg_color():
            color = colorchooser.askcolor(color=self.bg_color_var.get())
            if color[1]:
                self.bg_color_var.set(color[1])
                update_color_preview()
        
        ttk.Button(bg_color_frame, text="Pick", command=pick_bg_color, width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.bg_color_preview = tk.Canvas(bg_color_frame, width=30, height=30, 
                                          bg=self.bg_color_var.get(), relief=tk.SUNKEN, bd=1)
        self.bg_color_preview.pack(side=tk.LEFT)
        
        # Text color
        text_color_frame = ttk.Frame(gen_icon_frame)
        text_color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(text_color_frame, text="Text Color:", width=20).pack(side=tk.LEFT, padx=(0, 5))
        self.text_color_var = tk.StringVar(value="#FFFFFF")
        text_color_entry = ttk.Entry(text_color_frame, textvariable=self.text_color_var, width=15)
        text_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        def pick_text_color():
            color = colorchooser.askcolor(color=self.text_color_var.get())
            if color[1]:
                self.text_color_var.set(color[1])
                update_color_preview()
        
        ttk.Button(text_color_frame, text="Pick", command=pick_text_color, width=8).pack(side=tk.LEFT, padx=(0, 5))
        self.text_color_preview = tk.Canvas(text_color_frame, width=30, height=30,
                                            bg=self.text_color_var.get(), relief=tk.SUNKEN, bd=1)
        self.text_color_preview.pack(side=tk.LEFT)
        
        # Bold text option
        self.bold_icon_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(gen_icon_frame, text="Bold Text", variable=self.bold_icon_var).pack(anchor=tk.W, pady=(0, 5))
        
        # Gradient option
        self.gradient_icon_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(gen_icon_frame, text="Add Gradient Effect", variable=self.gradient_icon_var).pack(anchor=tk.W)
        
        def update_color_preview():
            try:
                self.bg_color_preview.config(bg=self.bg_color_var.get())
                self.text_color_preview.config(bg=self.text_color_var.get())
            except:
                pass
        
        # Custom icon upload
        custom_icon_frame = ttk.LabelFrame(options_frame, text="Custom Icon (Optional)", padding="10")
        custom_icon_frame.pack(fill=tk.X, pady=(0, 10))
        
        custom_icon_inner = ttk.Frame(custom_icon_frame)
        custom_icon_inner.pack(fill=tk.X)
        
        self.custom_icon_path_var = tk.StringVar()
        custom_icon_entry = ttk.Entry(custom_icon_inner, textvariable=self.custom_icon_path_var, width=40)
        custom_icon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def browse_custom_icon():
            filepath = filedialog.askopenfilename(
                title="Select Custom Icon",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.svg *.ico"), ("All Files", "*.*")]
            )
            if filepath:
                self.custom_icon_path_var.set(filepath)
        
        ttk.Button(custom_icon_inner, text="Browse", command=browse_custom_icon, width=10).pack(side=tk.LEFT)
        
        # System icon name (for system icons)
        sys_icon_frame = ttk.LabelFrame(options_frame, text="System Icon Name (Optional)", padding="10")
        sys_icon_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sys_icon_frame, text="Icon Name:").pack(anchor=tk.W, pady=(0, 5))
        self.icon_name_var = tk.StringVar()
        icon_entry = ttk.Entry(sys_icon_frame, textvariable=self.icon_name_var, width=40)
        icon_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(sys_icon_frame, text="(e.g., python, application-x-python, etc.)", 
                 foreground="#666666", font=("Arial", 9)).pack(anchor=tk.W)
        
        # Categories selection
        cat_label_frame = ttk.Frame(options_frame)
        cat_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(cat_label_frame, text="Categories:", width=20).pack(side=tk.LEFT, padx=(0, 5))
        self.categories_var = tk.StringVar(value="Development")
        categories_entry = ttk.Entry(cat_label_frame, textvariable=self.categories_var, width=30)
        categories_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(cat_label_frame, text="(e.g., Development, Utility, Office, etc.)", 
                 foreground="#666666", font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Terminal checkbox
        self.terminal_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Run in terminal",
            variable=self.terminal_var
        ).pack(anchor=tk.W)
        
        # Console output for desktop operations
        console_frame = ttk.LabelFrame(container, text="Desktop File Operations Log", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.desktop_console = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            height=8,
            font=("Monospace", 9),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white'
        )
        self.desktop_console.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.desktop_console.tag_config('info', foreground='#569cd6')
        self.desktop_console.tag_config('success', foreground='#4ec9b0')
        self.desktop_console.tag_config('error', foreground='#f44747')
        self.desktop_console.tag_config('warning', foreground='#dcdcaa')
        
        # Refresh desktop files list when tab is selected
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Initial refresh
        self.refresh_desktop_files_list()
    
    def on_tab_changed(self, event):
        """Handle tab changes"""
        selected_tab = self.notebook.index("current")
        if selected_tab == 1:  # Desktop Files tab
            self.refresh_desktop_files_list()
    
    def create_controls_panel(self, parent):
        """Create the controls panel"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content
        frame = scrollable_frame
        
        # Title
        ttk.Label(
            frame,
            text="Configure Python App",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 15))
        
        # Virtual Environment
        venv_frame = ttk.LabelFrame(frame, text="Virtual Environment", padding="10")
        venv_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(venv_frame, text="VENV Path:").pack(anchor=tk.W, pady=(0, 5))
        
        venv_entry = ttk.Entry(venv_frame, textvariable=self.venv_path_var, width=40)
        venv_entry.pack(fill=tk.X, pady=(0, 5))
        
        venv_buttons = ttk.Frame(venv_frame)
        venv_buttons.pack(fill=tk.X)
        
        ttk.Button(
            venv_buttons,
            text="Browse",
            command=self.browse_venv,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            venv_buttons,
            text="Auto Detect",
            command=self.auto_detect_venv,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            venv_buttons,
            text="Test Activation",
            command=self.test_venv_activation,
            width=14
        ).pack(side=tk.LEFT)
        
        # Python Script
        script_frame = ttk.LabelFrame(frame, text="Python Script", padding="10")
        script_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(script_frame, text="Script Path:").pack(anchor=tk.W, pady=(0, 5))
        
        script_entry = ttk.Entry(script_frame, textvariable=self.script_path_var, width=40)
        script_entry.pack(fill=tk.X, pady=(0, 5))
        
        script_buttons = ttk.Frame(script_frame)
        script_buttons.pack(fill=tk.X)
        
        ttk.Button(
            script_buttons,
            text="Browse",
            command=self.browse_script,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            script_buttons,
            text="Test Run",
            command=self.test_script_run,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Arguments
        args_frame = ttk.LabelFrame(frame, text="Script Arguments", padding="10")
        args_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(args_frame, textvariable=self.args_var).pack(fill=tk.X)
        
        # Working Directory
        workdir_frame = ttk.LabelFrame(frame, text="Working Directory", padding="10")
        workdir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(workdir_frame, textvariable=self.workdir_var).pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            workdir_frame,
            text="Browse",
            command=self.browse_workdir,
            width=12
        ).pack()
        
        # App Name
        appname_frame = ttk.LabelFrame(frame, text="Application Name", padding="10")
        appname_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(appname_frame, textvariable=self.app_name_var).pack(fill=tk.X)
        
        # Action Buttons
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            action_frame,
            text="💾 Save & Create Script",
            command=self.save_and_create_script,
            width=20
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="▶ Run Now",
            command=self.run_now,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Clear Fields",
            command=self.clear_fields,
            width=15
        ).pack(side=tk.LEFT)
    
    def create_apps_list(self, parent):
        """Create the saved apps list"""
        # Treeview for apps
        columns = ("name", "venv", "script", "created")
        self.apps_tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)
        
        # Define headings
        self.apps_tree.heading("name", text="App Name")
        self.apps_tree.heading("venv", text="Virtual Environment")
        self.apps_tree.heading("script", text="Script")
        self.apps_tree.heading("created", text="Created")
        
        # Define columns
        self.apps_tree.column("name", width=120)
        self.apps_tree.column("venv", width=100)
        self.apps_tree.column("script", width=150)
        self.apps_tree.column("created", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.apps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.apps_tree.bind('<<TreeviewSelect>>', self.on_app_selected)
        
        # Action buttons for selected app
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            action_frame,
            text="▶ Run Selected",
            command=self.run_selected_app,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="📋 Load Selected",
            command=self.load_selected_app,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="🗑 Delete Selected",
            command=self.delete_selected_app,
            width=15
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            action_frame,
            text="📂 Open Script Folder",
            command=self.open_script_folder,
            width=18
        ).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_output_console(self, parent):
        """Create the output console"""
        self.output_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            height=15,
            font=("Monospace", 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.output_text.tag_config('info', foreground='#569cd6')
        self.output_text.tag_config('success', foreground='#4ec9b0')
        self.output_text.tag_config('error', foreground='#f44747')
        self.output_text.tag_config('command', foreground='#dcdcaa')
        
        # Clear button
        ttk.Button(
            parent,
            text="Clear Console",
            command=self.clear_console,
            width=15
        ).pack(pady=(5, 0))
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-s>', lambda e: self.save_and_create_script())
        self.root.bind('<Control-r>', lambda e: self.run_now())
        self.root.bind('<Control-l>', lambda e: self.clear_console())
        self.root.bind('<Control-d>', lambda e: self.clear_fields())
        self.root.bind('<F5>', lambda e: self.refresh_apps_list())
    
    # =====================================================
    # File Browsing Functions
    # =====================================================
    
    def browse_venv(self):
        """Browse for virtual environment directory"""
        venv_dir = filedialog.askdirectory(
            title="Select Virtual Environment Directory",
            initialdir=os.path.expanduser("~")
        )
        if venv_dir:
            self.venv_path_var.set(venv_dir)
            self.log_to_console(f"Selected VENV: {os.path.basename(venv_dir)}", 'info')
    
    def browse_script(self):
        """Browse for Python script"""
        script_file = filedialog.askopenfilename(
            title="Select Python Script",
            initialdir=os.path.expanduser("~"),
            filetypes=[
                ("Python files", "*.py *.pyw"),
                ("All files", "*.*")
            ]
        )
        if script_file:
            self.script_path_var.set(script_file)
            self.log_to_console(f"Selected script: {os.path.basename(script_file)}", 'info')
            
            # Auto-fill app name if empty
            if not self.app_name_var.get():
                name = os.path.basename(script_file).replace('.py', '').replace('_', ' ').title()
                self.app_name_var.set(name)
    
    def browse_workdir(self):
        """Browse for working directory"""
        workdir = filedialog.askdirectory(
            title="Select Working Directory",
            initialdir=self.workdir_var.get()
        )
        if workdir:
            self.workdir_var.set(workdir)
            self.log_to_console(f"Working directory: {workdir}", 'info')
    
    def auto_detect_venv(self):
        """Auto-detect virtual environments"""
        venvs = self.find_virtual_environments()
        
        if not venvs:
            self.log_to_console("No virtual environments found.", 'info')
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Virtual Environment")
        dialog.geometry("600x400")
        
        # Listbox
        listbox = tk.Listbox(dialog, font=("Monospace", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for venv in venvs:
            listbox.insert(tk.END, f"{os.path.basename(venv):20} → {venv}")
        
        def select_venv():
            selection = listbox.curselection()
            if selection:
                venv_str = listbox.get(selection[0])
                # Extract path (part after →)
                if '→' in venv_str:
                    venv_path = venv_str.split('→', 1)[1].strip()
                else:
                    venv_path = venv_str.strip()
                
                self.venv_path_var.set(venv_path)
                self.log_to_console(f"Auto-selected VENV: {os.path.basename(venv_path)}", 'success')
                dialog.destroy()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Select", command=select_venv, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT)
    
    def find_virtual_environments(self):
        """Find virtual environments in common locations"""
        venvs = []
        common_paths = [
            os.path.expanduser("~"),
            os.path.expanduser("~/venvs"),
            os.path.expanduser("~/.virtualenvs"),
            os.path.expanduser("~/Envs"),
            os.getcwd(),
            os.path.join(os.getcwd(), "venv"),
            os.path.join(os.getcwd(), ".venv"),
            os.path.join(os.getcwd(), "env"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                try:
                    for item in os.listdir(path):
                        full_path = os.path.join(path, item)
                        if os.path.isdir(full_path):
                            # Check if it's a virtual environment
                            if self.is_virtual_environment(full_path):
                                venvs.append(full_path)
                except:
                    continue
        
        return venvs
    
    def is_virtual_environment(self, path):
        """Check if a directory is a virtual environment"""
        indicators = [
            os.path.join(path, "pyvenv.cfg"),
            os.path.join(path, "bin", "activate"),
            os.path.join(path, "Scripts", "activate.bat"),
            os.path.join(path, "Scripts", "activate.ps1"),
        ]
        return any(os.path.exists(indicator) for indicator in indicators)
    
    # =====================================================
    # Core Functions - Script Creation and Execution
    # =====================================================
    
    def create_activation_script(self, app_config):
        """Create an activation script for the app"""
        app_name = app_config['name']
        venv_path = app_config['venv']
        script_path = app_config['script']
        args = app_config.get('args', '')
        workdir = app_config.get('workdir', os.path.dirname(script_path))
        
        # Generate script filename
        safe_name = app_name.lower().replace(' ', '_').replace('-', '_')
        script_filename = f"{safe_name}.sh"
        script_filepath = os.path.join(self.scripts_dir, script_filename)
        
        # Determine activation command based on OS
        if platform.system() == "Windows":
            # Windows version
            script_content = f"""@echo off
echo Running {app_name}...
echo.

REM Change to working directory
cd /D "{workdir}"

REM Activate virtual environment
echo Activating virtual environment...
call "{os.path.join(venv_path, 'Scripts', 'activate.bat')}"

REM Run the Python script
echo Running script: {os.path.basename(script_path)}
python "{script_path}" {args}

REM Keep window open
echo.
echo Script execution complete.
pause
"""
        else:
            # Linux/macOS version
            script_content = f"""#!/bin/bash
echo "Running {app_name}..."
echo ""

# Change to working directory
cd "{workdir}"

# Activate virtual environment
echo "Activating virtual environment..."
source "{os.path.join(venv_path, 'bin', 'activate')}"

# Run the Python script
echo "Running script: {os.path.basename(script_path)}"
python3 "{script_path}" {args}

# Keep terminal open
echo ""
echo "Script execution complete."
read -p "Press Enter to exit..."
"""
        
        # Write script to file
        with open(script_filepath, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(script_filepath, 0o755)
        
        self.log_to_console(f"Created activation script: {script_filename}", 'success')
        return script_filepath
    
    def create_xterm_launcher(self, app_config, activation_script):
        """Create a launcher that opens xterm with the activation script"""
        app_name = app_config['name']
        safe_name = app_name.lower().replace(' ', '_').replace('-', '_')
        launcher_filename = f"launch_{safe_name}.sh"
        launcher_filepath = os.path.join(self.scripts_dir, launcher_filename)
        
        if platform.system() == "Windows":
            # Windows - create batch file
            launcher_content = f"""@echo off
start "Running {app_name}" cmd /K "{activation_script}"
"""
        else:
            # Linux - create shell script with xterm
            launcher_content = f"""#!/bin/bash
xterm -title "Running: {app_name}" -geometry 100x30 -e "bash -i '{activation_script}'" &
"""
        
        # Write launcher
        with open(launcher_filepath, 'w') as f:
            f.write(launcher_content)
        
        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(launcher_filepath, 0o755)
        
        self.log_to_console(f"Created launcher: {launcher_filename}", 'success')
        return launcher_filepath
    
    def save_and_create_script(self):
        """Save app configuration and create activation script"""
        app_name = self.app_name_var.get().strip()
        venv_path = self.venv_path_var.get().strip()
        script_path = self.script_path_var.get().strip()
        
        if not app_name:
            messagebox.showerror("Error", "Please enter an app name!")
            return
        
        if not venv_path:
            messagebox.showerror("Error", "Please select a virtual environment!")
            return
        
        if not script_path:
            messagebox.showerror("Error", "Please select a Python script!")
            return
        
        if not os.path.exists(venv_path):
            messagebox.showerror("Error", f"Virtual environment not found: {venv_path}")
            return
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found: {script_path}")
            return
        
        # Create app configuration
        app_config = {
            'name': app_name,
            'venv': venv_path,
            'script': script_path,
            'args': self.args_var.get().strip(),
            'workdir': self.workdir_var.get().strip(),
            'created': datetime.now().isoformat(),
            'last_run': None
        }
        
        # Check if app already exists
        existing_index = -1
        for i, app in enumerate(self.saved_apps):
            if app['name'] == app_name:
                existing_index = i
                break
        
        if existing_index >= 0:
            if not messagebox.askyesno("Confirm", f"App '{app_name}' already exists. Overwrite?"):
                return
            self.saved_apps[existing_index] = app_config
        else:
            self.saved_apps.append(app_config)
        
        # Save apps to file
        self.save_apps()
        
        # Create activation script
        activation_script = self.create_activation_script(app_config)
        
        # Create xterm launcher
        launcher_script = self.create_xterm_launcher(app_config, activation_script)
        
        # Update status
        app_config['activation_script'] = activation_script
        app_config['launcher_script'] = launcher_script
        
        # Refresh apps list
        self.refresh_apps_list()
        
        # Show success message
        self.log_to_console(f"✓ App '{app_name}' saved and scripts created", 'success')
        self.log_to_console(f"  Activation script: {os.path.basename(activation_script)}", 'info')
        self.log_to_console(f"  Launcher script: {os.path.basename(launcher_script)}", 'info')
        
        # Ask if user wants to run it now
        if messagebox.askyesno("Success", 
            f"App '{app_name}' has been saved!\n\n"
            f"Created activation script: {os.path.basename(activation_script)}\n"
            f"Created launcher script: {os.path.basename(launcher_script)}\n\n"
            "Do you want to run it now?"):
            self.run_script_file(launcher_script)
    
    def run_now(self):
        """Run the current configuration immediately"""
        app_name = self.app_name_var.get().strip()
        venv_path = self.venv_path_var.get().strip()
        script_path = self.script_path_var.get().strip()
        
        if not venv_path:
            messagebox.showerror("Error", "Please select a virtual environment!")
            return
        
        if not script_path:
            messagebox.showerror("Error", "Please select a Python script!")
            return
        
        # Create temporary app config
        if not app_name:
            app_name = f"Temp_{datetime.now().strftime('%H%M%S')}"
        
        app_config = {
            'name': app_name,
            'venv': venv_path,
            'script': script_path,
            'args': self.args_var.get().strip(),
            'workdir': self.workdir_var.get().strip(),
            'created': datetime.now().isoformat()
        }
        
        # Create temporary activation script
        temp_script = self.create_activation_script(app_config)
        
        # Run it
        self.run_script_file(temp_script)
    
    def run_script_file(self, script_path):
        """Run a script file"""
        if not os.path.exists(script_path):
            self.log_to_console(f"Error: Script not found: {script_path}", 'error')
            return
        
        try:
            if platform.system() == "Windows":
                # Windows
                subprocess.Popen(['start', 'cmd', '/K', script_path], shell=True)
                self.log_to_console(f"✓ Launched in new terminal: {os.path.basename(script_path)}", 'success')
            else:
                # Linux/macOS
                subprocess.Popen(['xterm', '-title', 'Python App Launcher', '-geometry', '100x30', 
                                 '-e', f'bash -i "{script_path}"'], 
                                start_new_session=True)
                self.log_to_console(f"✓ Launched in xterm: {os.path.basename(script_path)}", 'success')
        except Exception as e:
            self.log_to_console(f"Error launching terminal: {str(e)}", 'error')
            # Fallback: try running directly
            try:
                subprocess.Popen(['bash', script_path], start_new_session=True)
                self.log_to_console("✓ Launched with fallback method", 'success')
            except Exception as e2:
                self.log_to_console(f"Fallback also failed: {str(e2)}", 'error')
    
    def run_selected_app(self):
        """Run the selected saved app"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to run!")
            return
        
        item = self.apps_tree.item(selection[0])
        app_name = item['values'][0]
        
        # Find the app
        for app in self.saved_apps:
            if app['name'] == app_name:
                # Update last run time
                app['last_run'] = datetime.now().isoformat()
                self.save_apps()
                
                # Check if launcher script exists
                if 'launcher_script' in app and os.path.exists(app['launcher_script']):
                    self.run_script_file(app['launcher_script'])
                else:
                    # Create new launcher
                    activation_script = self.create_activation_script(app)
                    launcher_script = self.create_xterm_launcher(app, activation_script)
                    app['activation_script'] = activation_script
                    app['launcher_script'] = launcher_script
                    self.save_apps()
                    self.run_script_file(launcher_script)
                
                self.log_to_console(f"✓ Running app: {app_name}", 'success')
                break
    
    # =====================================================
    # Utility Functions
    # =====================================================
    
    def test_venv_activation(self):
        """Test if virtual environment can be activated"""
        venv_path = self.venv_path_var.get().strip()
        
        if not venv_path:
            messagebox.showwarning("Warning", "Please select a virtual environment!")
            return
        
        if not os.path.exists(venv_path):
            messagebox.showerror("Error", f"Virtual environment not found: {venv_path}")
            return
        
        # Check activation script exists
        if platform.system() == "Windows":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")
        
        if not os.path.exists(activate_script):
            self.log_to_console(f"✗ Activation script not found: {activate_script}", 'error')
            return
        
        # Test Python executable
        if platform.system() == "Windows":
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")
        
        if not os.path.exists(python_exe):
            python_exe = os.path.join(venv_path, "bin", "python3")
        
        if os.path.exists(python_exe):
            try:
                result = subprocess.run([python_exe, "--version"], 
                                      capture_output=True, text=True)
                version = result.stdout.strip()
                self.log_to_console(f"✓ VENV Python: {version}", 'success')
            except:
                self.log_to_console(f"✓ VENV Python found but version check failed", 'info')
        else:
            self.log_to_console(f"✗ Python executable not found in VENV", 'error')
        
        self.log_to_console(f"✓ Virtual environment is valid: {os.path.basename(venv_path)}", 'success')
    
    def test_script_run(self):
        """Test if script can be run"""
        script_path = self.script_path_var.get().strip()
        
        if not script_path:
            messagebox.showwarning("Warning", "Please select a Python script!")
            return
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found: {script_path}")
            return
        
        # Check if it's a Python file
        if not script_path.endswith('.py'):
            self.log_to_console("⚠ File doesn't have .py extension, but will try anyway", 'info')
        
        # Try to parse the script for imports
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Simple check for shebang
            if content.startswith('#!/usr/bin/env python'):
                self.log_to_console("✓ Script has Python shebang", 'success')
            elif 'import ' in content or 'from ' in content:
                self.log_to_console("✓ Script contains Python imports", 'success')
            else:
                self.log_to_console("⚠ Script doesn't appear to have Python imports", 'info')
            
            self.log_to_console(f"✓ Script is readable: {os.path.basename(script_path)}", 'success')
            
        except Exception as e:
            self.log_to_console(f"✗ Cannot read script: {str(e)}", 'error')
    
    def load_selected_app(self):
        """Load selected app configuration into the form"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to load!")
            return
        
        item = self.apps_tree.item(selection[0])
        app_name = item['values'][0]
        
        # Find the app
        for app in self.saved_apps:
            if app['name'] == app_name:
                self.app_name_var.set(app['name'])
                self.venv_path_var.set(app.get('venv', ''))
                self.script_path_var.set(app.get('script', ''))
                self.args_var.set(app.get('args', ''))
                self.workdir_var.set(app.get('workdir', os.getcwd()))
                
                self.log_to_console(f"✓ Loaded app: {app_name}", 'success')
                break
    
    def delete_selected_app(self):
        """Delete selected app"""
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to delete!")
            return
        
        item = self.apps_tree.item(selection[0])
        app_name = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete app '{app_name}'?\n\nThis will also delete the activation scripts."):
            # Find and delete script files
            for app in self.saved_apps:
                if app['name'] == app_name:
                    # Delete activation script if exists
                    if 'activation_script' in app and os.path.exists(app['activation_script']):
                        try:
                            os.remove(app['activation_script'])
                            self.log_to_console(f"Deleted: {os.path.basename(app['activation_script'])}", 'info')
                        except:
                            pass
                    
                    # Delete launcher script if exists
                    if 'launcher_script' in app and os.path.exists(app['launcher_script']):
                        try:
                            os.remove(app['launcher_script'])
                            self.log_to_console(f"Deleted: {os.path.basename(app['launcher_script'])}", 'info')
                        except:
                            pass
                    break
            
            # Remove from list
            self.saved_apps = [app for app in self.saved_apps if app['name'] != app_name]
            
            # Save to file
            self.save_apps()
            
            # Refresh list
            self.refresh_apps_list()
            
            self.log_to_console(f"✓ Deleted app: {app_name}", 'success')
    
    def open_script_folder(self):
        """Open the scripts folder"""
        if os.path.exists(self.scripts_dir):
            if platform.system() == "Windows":
                os.startfile(self.scripts_dir)
            else:
                subprocess.Popen(['xdg-open', self.scripts_dir])
            self.log_to_console(f"Opened scripts folder: {self.scripts_dir}", 'info')
        else:
            self.log_to_console("Scripts folder not found", 'error')
    
    def clear_fields(self):
        """Clear all input fields"""
        self.app_name_var.set("")
        self.venv_path_var.set("")
        self.script_path_var.set("")
        self.args_var.set("")
        self.workdir_var.set(os.getcwd())
        self.log_to_console("✓ Fields cleared", 'success')
    
    def clear_console(self):
        """Clear the console output"""
        self.output_text.delete(1.0, tk.END)
        self.log_to_console("Console cleared", 'info')
    
    def log_to_console(self, message, tag='info'):
        """Log message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.output_text.see(tk.END)
    
    def refresh_apps_list(self):
        """Refresh the apps list"""
        if not hasattr(self, 'apps_tree'):
            return
        
        # Clear current items
        for item in self.apps_tree.get_children():
            self.apps_tree.delete(item)
        
        # Add apps to treeview
        for app in self.saved_apps:
            venv_name = os.path.basename(app.get('venv', '')) if app.get('venv') else "System"
            script_name = os.path.basename(app.get('script', ''))
            
            # Format creation time
            created = app.get('created')
            if created:
                try:
                    created_time = datetime.fromisoformat(created)
                    created_str = created_time.strftime("%m/%d")
                except:
                    created_str = "Unknown"
            else:
                created_str = "Unknown"
            
            self.apps_tree.insert(
                '', 'end',
                values=(app['name'], venv_name, script_name, created_str)
            )
        
        self.log_to_console(f"Refreshed apps list ({len(self.saved_apps)} apps)", 'info')
    
    def on_app_selected(self, event):
        """Handle app selection"""
        pass
    
    def save_apps(self):
        """Save apps to file"""
        try:
            with open(self.apps_file, 'w') as f:
                json.dump(self.saved_apps, f, indent=2)
        except Exception as e:
            self.log_to_console(f"Error saving apps: {str(e)}", 'error')
    
    def load_apps(self):
        """Load apps from file"""
        try:
            if os.path.exists(self.apps_file):
                with open(self.apps_file, 'r') as f:
                    self.saved_apps = json.load(f)
                self.refresh_apps_list()
                self.log_to_console(f"Loaded {len(self.saved_apps)} saved apps", 'success')
        except:
            self.saved_apps = []
    
    # =====================================================
    # Desktop File Functions
    # =====================================================
    
    def get_desktop_files_dir(self):
        """Get the desktop files directory (~/.local/share/applications/)"""
        return os.path.join(os.path.expanduser("~"), ".local", "share", "applications")
    
    def create_desktop_file(self, app_config):
        """Create a .desktop file for the application with icon generation"""
        desktop_dir = self.get_desktop_files_dir()
        os.makedirs(desktop_dir, exist_ok=True)
        
        app_name = app_config['name']
        safe_name = app_name.lower().replace(' ', '_').replace('-', '_')
        desktop_filename = f"{safe_name}.desktop"
        desktop_filepath = os.path.join(desktop_dir, desktop_filename)
        
        # Get launcher script path
        if 'launcher_script' in app_config:
            launcher_script = app_config['launcher_script']
        else:
            # Create activation script if it doesn't exist
            launcher_script = self.create_activation_script(app_config)
        
        # Prepare the Exec line
        exec_command = f"bash -i '{launcher_script}'"
        
        # Handle icon generation based on selected type
        icon_name = "application-x-python"  # Default fallback
        icon_type = getattr(self, 'icon_type_var', tk.StringVar()).get() or "generate"
        
        if icon_type == "generate":
            # Generate icon with selected colors
            try:
                bg_color = getattr(self, 'bg_color_var', tk.StringVar()).get() or "#4285F4"
                text_color = getattr(self, 'text_color_var', tk.StringVar()).get() or "#FFFFFF"
                bold = getattr(self, 'bold_icon_var', tk.BooleanVar()).get()
                with_gradient = getattr(self, 'gradient_icon_var', tk.BooleanVar()).get()
                
                icon_gen = IconGenerator(size=256)
                icon_path = IconGenerator.get_icon_path(app_name)
                
                icon_gen.generate_icon(
                    app_name,
                    bg_color=bg_color,
                    text_color=text_color,
                    bold=bold,
                    output_path=icon_path,
                    with_gradient=with_gradient
                )
                
                icon_name = icon_path
                app_config['icon_path'] = icon_path
                app_config['icon_type'] = 'generated'
                app_config['icon_settings'] = {
                    'bg_color': bg_color,
                    'text_color': text_color,
                    'bold': bold,
                    'gradient': with_gradient
                }
                
                self.desktop_log(f"✓ Generated icon for {app_name}: {icon_path}", 'success')
            except Exception as e:
                self.desktop_log(f"⚠ Could not generate icon: {str(e)}", 'warning')
                icon_name = "application-x-python"
        
        elif icon_type == "custom":
            # Use custom icon
            custom_icon = getattr(self, 'custom_icon_path_var', tk.StringVar()).get()
            if custom_icon and os.path.exists(custom_icon):
                icon_name = custom_icon
                app_config['icon_path'] = custom_icon
                app_config['icon_type'] = 'custom'
                self.desktop_log(f"✓ Using custom icon: {custom_icon}", 'success')
            else:
                self.desktop_log("⚠ Custom icon not found, using default", 'warning')
                icon_name = "application-x-python"
        
        else:  # system
            # Use system icon name
            sys_icon = getattr(self, 'icon_name_var', tk.StringVar()).get()
            if sys_icon:
                icon_name = sys_icon
                app_config['icon_type'] = 'system'
                app_config['icon_name'] = sys_icon
                self.desktop_log(f"✓ Using system icon: {sys_icon}", 'success')
        
        # Get categories
        categories = getattr(self, 'categories_var', tk.StringVar()).get() or "Development"
        
        # Determine if should run in terminal
        terminal = getattr(self, 'terminal_var', tk.BooleanVar()).get()
        
        # Create desktop file content
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=Python application - {app_name}
Exec={exec_command}
Icon={icon_name}
Terminal={str(terminal).lower()}
Categories={categories}
StartupNotify=true
Version=1.0
Path={app_config.get('workdir', os.path.dirname(app_config.get('script', '')))}
"""
        
        # Write desktop file
        try:
            with open(desktop_filepath, 'w') as f:
                f.write(desktop_content)
            
            # Make it executable
            os.chmod(desktop_filepath, 0o755)
            
            # Update app config
            app_config['desktop_file'] = desktop_filepath
            
            self.desktop_log(f"✓ Created desktop file: {desktop_filename}", 'success')
            return desktop_filepath
        except Exception as e:
            self.desktop_log(f"✗ Error creating desktop file: {str(e)}", 'error')
            return None
    
    
    def generate_selected_desktop_file(self):
        """Generate desktop file for selected app"""
        if not hasattr(self, 'desktop_tree'):
            self.desktop_log("Desktop Files tab not initialized", 'error')
            return
        
        selection = self.desktop_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to generate desktop file for!")
            return
        
        item = self.desktop_tree.item(selection[0])
        app_name = item['values'][0]
        
        # Find the app
        for app in self.saved_apps:
            if app['name'] == app_name:
                desktop_path = self.create_desktop_file(app)
                if desktop_path:
                    self.save_apps()
                    self.refresh_desktop_files_list()
                    self.desktop_log(f"✓ Desktop file ready for: {app_name}", 'success')
                    self.desktop_log(f"  Location: {desktop_path}", 'info')
                    messagebox.showinfo("Success", 
                        f"Desktop file created!\n\n"
                        f"File: {os.path.basename(desktop_path)}\n"
                        f"Location: {os.path.dirname(desktop_path)}\n\n"
                        f"The application should now appear in your Applications menu.\n"
                        f"You may need to refresh your app menu (press Super key and search).")
                return
    
    def generate_and_refresh_desktop(self):
        """Generate desktop files for all saved apps and refresh"""
        if not self.saved_apps:
            messagebox.showinfo("Info", "No saved applications to generate desktop files for.")
            return
        
        created_count = 0
        error_count = 0
        
        self.desktop_log("Starting desktop file generation for all apps...", 'info')
        
        for app in self.saved_apps:
            desktop_path = self.create_desktop_file(app)
            if desktop_path:
                created_count += 1
            else:
                error_count += 1
        
        self.save_apps()
        self.refresh_desktop_files_list()
        
        # Update desktop database
        self.update_desktop_database()
        
        self.desktop_log(f"✓ Generation complete: {created_count} created, {error_count} failed", 'success')
        
        messagebox.showinfo("Success",
            f"Desktop files generated!\n\n"
            f"Created: {created_count}\n"
            f"Failed: {error_count}\n\n"
            f"Your applications should now appear in the Applications menu.")
    
    def update_desktop_database(self):
        """Update the desktop database"""
        try:
            subprocess.run(['update-desktop-database', self.get_desktop_files_dir()], 
                         capture_output=True, timeout=5)
            self.desktop_log("✓ Desktop database updated", 'success')
        except Exception as e:
            self.desktop_log(f"⚠ Could not update desktop database: {str(e)}", 'warning')
    
    def delete_desktop_file(self):
        """Delete desktop file for selected app"""
        if not hasattr(self, 'desktop_tree'):
            self.desktop_log("Desktop Files tab not initialized", 'error')
            return
        
        selection = self.desktop_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app!")
            return
        
        item = self.desktop_tree.item(selection[0])
        app_name = item['values'][0]
        
        if messagebox.askyesno("Confirm", f"Delete desktop file for '{app_name}'?"):
            for app in self.saved_apps:
                if app['name'] == app_name:
                    if 'desktop_file' in app:
                        try:
                            if os.path.exists(app['desktop_file']):
                                os.remove(app['desktop_file'])
                                self.desktop_log(f"✓ Deleted: {os.path.basename(app['desktop_file'])}", 'success')
                            del app['desktop_file']
                            self.save_apps()
                        except Exception as e:
                            self.desktop_log(f"✗ Error deleting desktop file: {str(e)}", 'error')
                    break
            
            self.refresh_desktop_files_list()
    
    def open_desktop_files_folder(self):
        """Open the desktop files folder"""
        desktop_dir = self.get_desktop_files_dir()
        if os.path.exists(desktop_dir):
            try:
                subprocess.Popen(['xdg-open', desktop_dir])
                self.desktop_log(f"Opened desktop files folder: {desktop_dir}", 'info')
            except Exception as e:
                self.desktop_log(f"Could not open folder: {str(e)}", 'error')
        else:
            self.desktop_log("Desktop files folder not found", 'error')
    
    def refresh_desktop_files_list(self):
        """Refresh the desktop files list"""
        if not hasattr(self, 'desktop_tree'):
            return
        
        # Clear current items
        for item in self.desktop_tree.get_children():
            self.desktop_tree.delete(item)
        
        desktop_dir = self.get_desktop_files_dir()
        
        # Add apps to treeview with desktop file status
        for app in self.saved_apps:
            created = app.get('created')
            if created:
                try:
                    created_time = datetime.fromisoformat(created)
                    created_str = created_time.strftime("%m/%d %H:%M")
                except:
                    created_str = "Unknown"
            else:
                created_str = "Unknown"
            
            # Check desktop file status
            if 'desktop_file' in app and os.path.exists(app['desktop_file']):
                status = "✓ Generated"
            else:
                status = "○ Not Generated"
            
            self.desktop_tree.insert(
                '', 'end',
                values=(app['name'], status, created_str)
            )
    
    def desktop_log(self, message, tag='info'):
        """Log message to desktop console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, 'desktop_console'):
            self.desktop_console.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.desktop_console.see(tk.END)


def main():
    root = tk.Tk()
    
    # Set window icon if available
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = PythonAppLauncher(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()
    
