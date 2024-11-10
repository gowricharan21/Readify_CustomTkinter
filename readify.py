import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import json
import re
from pathlib import Path
import PyPDF2
from PIL import Image, ImageTk
import fitz  
import threading
from datetime import datetime
import pickle
import os
import ctypes
from collections import deque
import customtkinter as ctk

class EbookReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Readify")
        style = ttk.Style()
        self.current_file = None
        self.bookmarks = {}
        self.search_results = []
        self.current_search_index = 0
        self.current_page = 0
        self.total_pages = 0
        self.reading_history = {}
        self.pdf_document = None
        self.current_zoom = 1.0
        self.annotations = {}
        self.last_searched_terms = []
        self.current_image = None
        self.search_history = deque(maxlen=10) 
        self.highlight_tags = [] 
        self.preferences = {'font_size': 12,'font_family': 'Arial','reading_position': {},'window_size': '1200x700'}
        self.load_data()
        self.setup_ui()
        self.setup_keyboard_shortcuts()
    def setup_keyboard_shortcuts(self):
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Control-b>', lambda e: self.toggle_sidebar())
        self.root.bind('<Control-h>', lambda e: self.show_search_history())
        self.root.bind('<Control-s>', lambda e: self.save_current_state())
        self.root.bind('<Control-r>', lambda e: self.reset_view())
        self.root.bind('<Control-t>', lambda e: self.toggle_theme())
    def save_current_state(self):
        """Save current reading state"""
        if self.current_file:
            self.preferences['reading_position'][self.current_file] = self.current_page
            self.save_data()
            self.show_info_message("Save", "Current reading state saved")
    def reset_view(self):
        """Reset view settings"""
        self.current_zoom = 1.0
        if self.pdf_document:
            self.load_pdf_page()
    def show_search_history(self):
        """Display search history"""
        if not self.search_history:
            self.show_info_message("Search History", "No search history available")
            return
        history_window = tk.Toplevel(self.root)
        history_window.title("Search History")
        history_window.geometry("300x400")
        listbox = tk.Listbox(history_window)
        listbox.pack(fill=tk.BOTH, expand=True)
        for term in reversed(self.search_history):
            listbox.insert(tk.END, term)  
        def use_selected():
            selection = listbox.curselection()
            if selection:
                term = listbox.get(selection[0])
                self.search_var.set(term)
                self.search_text()
                history_window.destroy()     
        ttk.Button(history_window, text="Use Selected", command=use_selected).pack(pady=5)
    def update_search(self):
        """Refresh the search with updated options."""
        search_term = self.search_var.get()
        if search_term:
            self.search_text()
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
    def search_text(self):
        """Enhanced search functionality with options"""
        search_term = self.search_var.get() 
        if not search_term:
            return
        if search_term not in self.search_history:
            self.search_history.append(search_term)
            self.search_combo['values'] = list(self.search_history)
        self.search_results.clear()
        self.current_search_index = 0 
        case_sensitive = self.case_sensitive_var.get()
        whole_word = self.whole_word_var.get()
        if self.pdf_document:
            self.search_pdf(search_term, case_sensitive, whole_word)
        else:
            self.search_text_document(search_term, case_sensitive, whole_word)
        self.update_search_display() 
    def focus_search(self):
        """Focus on search entry"""
        self.search_combo.focus_set()
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.preferences['theme'] == 'light':
            self.preferences['theme'] = 'dark'
            self.apply_dark_theme()
        else:
            self.preferences['theme'] = 'light'
            self.apply_light_theme()
        self.save_data()   
    def apply_dark_theme(self):
        style = ttk.Style()
        style.configure(".", background='#2d2d2d', foreground='#ffffff')
        style.configure("TEntry", fieldbackground='#3d3d3d', foreground='#ffffff')
        style.configure("TButton", background='#3d3d3d', foreground='#ffffff')
        self.text_area.configure(bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff')
    def apply_light_theme(self):
        style = ttk.Style()
        style.configure(".", background='#ffffff', foreground='#000000')
        style.configure("TEntry", fieldbackground='#ffffff', foreground='#000000')
        style.configure("TButton", background='#f0f0f0', foreground='#000000')
        self.text_area.configure(bg='#ffffff', fg='#000000', insertbackground='#000000')
    def setup_ui(self):
        self.create_menu()
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.setup_sidebar()
        self.setup_content_area()
        self.setup_status_bar()
        self.root.bind('<Control-plus>', lambda event: self.zoom(1.1))
        self.root.bind('<Control-minus>', lambda event: self.zoom(0.9))
        self.root.bind('<Left>', lambda event: self.prev_page())
        self.root.bind('<Right>', lambda event: self.next_page())
        self.root.bind('<Control-o>', lambda event: self.open_file())
        self.root.bind('<Enter>', lambda event: self.search_text())
        style=ttk.Style()
        style.configure("Search.TButton", background="#16347d", foreground="black",padding=6,relief="flat")  
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Recent Files", command=self.show_recent_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=lambda: self.zoom(1.1))
        view_menu.add_command(label="Zoom Out", command=lambda: self.zoom(0.9))
        view_menu.add_command(label="Reset Zoom", command=lambda: self.zoom(reset=True))
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Export Annotations", command=self.export_annotations)
        tools_menu.add_command(label="Reading Statistics", command=self.show_statistics)
    def setup_sidebar(self):
        self.sidebar = ttk.Notebook(self.main_container, width=300)
        self.main_container.add(self.sidebar, weight=0) 
        self.bookmark_frame = ttk.Frame(self.sidebar)
        self.sidebar.add(self.bookmark_frame, text="📚Bookmarks")
        ttk.Button(self.bookmark_frame, text=" + Add Bookmark", command=self.add_bookmark).pack(fill=tk.X, pady=5)
        self.bookmark_list = tk.Listbox(self.bookmark_frame, justify=tk.CENTER)
        self.bookmark_list.pack(fill=tk.BOTH, expand=True, pady=3)
        self.bookmark_list.bind('<<ListboxSelect>>', self.go_to_bookmark)
        self.toc_frame = ttk.Frame(self.sidebar)
        # self.sidebar.add(self.toc_frame, text="Contents")
        self.toc_tree = ttk.Treeview(self.toc_frame)
        self.toc_tree.pack(fill=tk.BOTH, expand=True)
        self.toc_tree.bind('<<TreeviewSelect>>', self.go_to_toc_item)
        self.notes_frame = ttk.Frame(self.sidebar)
        self.sidebar.add(self.notes_frame, text="📝Notes")
        self.setup_notes_ui()
        self.file_label = ttk.Label(self.sidebar, text="No file opened. Try to open a file and read", anchor="center")
        # self.file_label_window.attributes("-alpha", 0.7)
        self.file_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.search_var = tk.StringVar()
        
    def setup_content_area(self):
        self.content_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.content_frame, weight=3)
        self.setup_toolbar()
        self.content_notebook = ttk.Notebook(self.content_frame)
        self.content_notebook.pack(fill=tk.BOTH, expand=True)
        self.text_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.text_frame, text="Text View")
        self.text_area = tk.Text(self.text_frame, wrap=tk.WORD)
        text_scrollbar = ttk.Scrollbar(self.text_frame, command=self.text_area.yview)
        text_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.config(yscrollcommand=text_scrollbar.set)
        self.pdf_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(self.pdf_frame, text="PDF View")
        pdf_scroll_y = ttk.Scrollbar(self.pdf_frame, orient=tk.VERTICAL)
        pdf_scroll_x = ttk.Scrollbar(self.pdf_frame, orient=tk.HORIZONTAL)
        self.pdf_canvas = tk.Canvas(self.pdf_frame)
        pdf_scroll_y.pack(side=tk.LEFT, fill=tk.Y)
        pdf_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.pdf_canvas.pack(fill=tk.BOTH, expand=True)
        self.pdf_canvas.config(yscrollcommand=pdf_scroll_y.set, xscrollcommand=pdf_scroll_x.set)
        pdf_scroll_y.config(command=self.pdf_canvas.yview)
        pdf_scroll_x.config(command=self.pdf_canvas.xview)
        self.pdf_canvas.bind("<MouseWheel>", self.on_pdf_scroll)
    def create_toolbar_button(self, text, command, icon=None, tooltip=None):
        """Create a toolbar button with optional icon and tooltip"""
        btn = ttk.Button(self.toolbar, text=icon if icon else text, command=command)
        btn.pack(side=tk.LEFT, padx=2)
        if tooltip:
            self.create_tooltip(btn, tooltip)
    def create_tooltip(self, widget, text):
        """Create tooltip for widgets"""
        def enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            widget.tooltip = tooltip   
    def setup_toolbar(self):
        # style = ttk.Style()
        # self.toolbar = ttk.Frame(self.content_frame)
        # self.toolbar.pack(fill=tk.X, pady=5)
        # ttk.Button(self.toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        # self.page_var = tk.StringVar()
        # ttk.Label(self.toolbar, text="Page:").pack(side=tk.LEFT, padx=2)
        # self.page_entry = ttk.Entry(self.toolbar, textvariable=self.page_var, width=5)
        # self.page_entry.pack(side=tk.LEFT, padx=2)
        # self.page_total_label = ttk.Label(self.toolbar, text="/0")
        # self.page_total_label.pack(side=tk.LEFT, padx=2)
        # ttk.Button(self.toolbar, text="<", command=self.prev_page).pack(side=tk.LEFT, padx=2)
        # ttk.Button(self.toolbar, text=">", command=self.next_page).pack(side=tk.LEFT, padx=2)
        # ttk.Button(self.toolbar, text="+", command=lambda: self.zoom(1.1)).pack(side=tk.LEFT, padx=2)
        # ttk.Button(self.toolbar, text="-", command=lambda: self.zoom(0.9)).pack(side=tk.LEFT, padx=2)
        # self.search_var = tk.StringVar()
        # self.search_entry = ttk.Entry(self.toolbar, textvariable=self.search_var, width=30)
        # self.search_entry.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        # style.map(style="Search.TButton", background=[("active", "#1b4ea0")])
        # search_button = ttk.Button(self.toolbar, text="Search🔍", style="Search.TButton")
        # search_button.pack(side=tk.LEFT, padx=2)
        # search_button.bind("<Button-1>", lambda event: self.search_text())

        # ttk.Button(self.toolbar, text="Previous", command=self.prev_search_result).pack(side=tk.LEFT, padx=2)
        # ttk.Button(self.toolbar, text="Next", command=self.next_search_result).pack(side=tk.LEFT, padx=2)
        style = ttk.Style()
        self.toolbar = ttk.Frame(self.content_frame)
        self.toolbar.pack(fill=tk.X, pady=5)
        self.create_toolbar_button("Open", self.open_file, "📂", "Open a file (Ctrl+O)")
        self.create_toolbar_button("Save", self.save_current_state, "💾", "Save current state (Ctrl+S)")
        ttk.Separator(self.toolbar, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')
        self.page_var = tk.StringVar()
        ttk.Label(self.toolbar, text="Page:").pack(side=tk.LEFT, padx=2)
        self.page_entry = ttk.Entry(self.toolbar, textvariable=self.page_var, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_total_label = ttk.Label(self.toolbar, text="/0")
        self.page_total_label.pack(side=tk.LEFT, padx=2)
        self.create_toolbar_button("First", self.goto_first_page, "⏮", "Go to first page")
        self.create_toolbar_button("Prev", self.prev_page, "◀", "Previous page (Left Arrow)")
        self.create_toolbar_button("Next", self.next_page, "▶", "Next page (Right Arrow)")
        self.create_toolbar_button("Last", self.goto_last_page, "⏭", "Go to last page") 
        ttk.Separator(self.toolbar, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')
        self.create_toolbar_button("Zoom In", lambda: self.zoom(1.1), "🔍+", "Zoom in (Ctrl++)")
        self.create_toolbar_button("Zoom Out", lambda: self.zoom(0.9), "🔍-", "Zoom out (Ctrl+-)")
        # self.create_toolbar_button("Reset", lambda: self.zoom(reset=True), "🔍=", "Reset zoom (Ctrl+0)"
        self.setup_search_toolbar()
    def focus_search(self):
        """Focus on search entry"""
        self.search_combo.focus_set()
    def goto_first_page(self):
        """Go to first page"""
        self.current_page = 0
        self.load_pdf_page()
    def goto_last_page(self):
        """Go to last page"""
        if self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self.load_pdf_page()  
    def setup_search_toolbar(self):
        search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_var = tk.StringVar()
        self.search_combo = ttk.Combobox(search_frame, textvariable=self.search_var, width=30, values=list(self.search_history))
        self.search_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.case_sensitive_var = tk.BooleanVar()
        self.whole_word_var = tk.BooleanVar()
        for text, var in [("Aa", self.case_sensitive_var), ("W", self.whole_word_var)]:
            ttk.Checkbutton(search_frame, text=text, variable=var, command=self.update_search).pack(side=tk.LEFT)
        search_button = ctk.CTkButton(search_frame, text="Search🔍", command=self.search_text,fg_color="#2c3ff2", text_color="white", corner_radius=25,font=("Arial", 14), width=50)
        search_button.pack(side=tk.LEFT, padx=2)
        self.result_counter = ttk.Label(search_frame, text="0/0")
        self.result_counter.pack(side=tk.LEFT, padx=5)
        for text, command in [("↑", self.prev_search_result), ("↓", self.next_search_result)]:
            ctk.CTkButton(search_frame, text=text, command=command,fg_color="#587bed", text_color="white", corner_radius=50,font=("Arial", 12), width=10).pack(side=tk.LEFT, padx=5)
    def setup_status_bar(self):
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_bar, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    def setup_notes_ui(self):
        self.notes_text = tk.Text(self.notes_frame, height=10)
        notes_scrollbar = ttk.Scrollbar(self.notes_frame, command=self.notes_text.yview)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.config(yscrollcommand=notes_scrollbar.set)
        ttk.Button(self.notes_frame, text="Save Note", command=self.save_note).pack(fill=tk.X, pady=5)
        self.notes_list = tk.Listbox(self.notes_frame)
        self.notes_list.pack(fill=tk.BOTH, expand=True, pady=3)
        self.notes_list.bind('<<ListboxSelect>>', self.go_to_note)
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("All supported files", "*.txt *.pdf"),("Text files", "*.txt"),("PDF files", "*.pdf"),("All files", "*.*") ])
        if not file_path:
            return   
        self.current_file = file_path
        self.file_label.config(text=f"Opened: {os.path.basename(file_path)}")
        self.update_reading_history()
        if file_path.lower().endswith('.pdf'):
            self.open_pdf(file_path)
        else:
            self.open_text(file_path)   
    def open_pdf(self, file_path):
        try:
            self.pdf_document = fitz.open(file_path)
            self.total_pages = len(self.pdf_document)
            self.page_total_label.config(text=f"/{self.total_pages}")
            self.current_page = 0
            self.load_pdf_page()
            self.extract_pdf_toc()
            self.content_notebook.select(self.pdf_frame) 
            if file_path in self.preferences['reading_position']:
                self.current_page = self.preferences['reading_position'][file_path]
                self.load_pdf_page()
        except Exception as e:
            self.show_error_message("Error", f"Failed to open PDF: {str(e)}")
    def open_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(1.0, content)
            self.content_notebook.select(self.text_frame)
            self.update_bookmark_list()
        except Exception as e:
            self.show_error_message("Error", f"Failed to open text file: {str(e)}")           
    def zoom(self, factor=None, reset=False):
        if reset:
            self.current_zoom = 1.0
        elif factor:
            self.current_zoom *= factor       
        if self.pdf_document:
            self.load_pdf_page()
    def save_bookmarks(self):
        with open('bookmarks.json', 'w') as f:
            json.dump(self.bookmarks, f)
        with open('bookmarks.json', 'w') as f:
            json.dump(self.bookmarks, f)

    def load_bookmarks(self):
        if os.path.exists('bookmarks.json'):
            with open('bookmarks.json', 'r') as f:
                self.bookmarks = json.load(f)
            self.update_bookmark_list()
    def add_bookmark(self):
        if not self.current_file:
            self.show_warning_message("Warning", "Please open a file first")
            return
        if self.pdf_document:
            position = self.current_page
            context = f"Page {self.current_page + 1}"
        else:
            position = self.text_area.index(tk.INSERT)
            context = self.text_area.get("insert linestart", "insert lineend")
        bookmark_name = simpledialog.askstring("Add Bookmark", "Enter bookmark name:", initialvalue=context)
        if bookmark_name:
            self.bookmarks[bookmark_name] = (self.current_file, position)
            self.update_bookmark_list()
            self.save_data()
    def save_note(self):
        note_content = self.notes_text.get(1.0, tk.END).strip()
        if note_content:
            note_name = simpledialog.askstring("Save Note", "Enter note name:")
            if note_name:
                self.annotations[note_name] = note_content
                self.update_notes_list()
                self.save_data()
    def update_bookmark_list(self):
        self.bookmark_list.delete(0, tk.END)
        for index, name in enumerate(self.bookmarks, start=1):
            self.bookmark_list.insert(tk.END, f"{index} )  {name}")
    def update_notes_list(self):
        self.notes_list.delete(0, tk.END)
        for name in self.annotations:
            self.notes_list.insert(tk.END, name)
    def go_to_bookmark(self, event):
        selection = event.widget.curselection()
        if selection:
            bookmark_name = event.widget.get(selection[0])
            file_path, position = self.bookmarks[bookmark_name]
            if file_path != self.current_file:
                self.show_info_message("Info", "This bookmark is in another PDF.")
                self.open_file(file_path)
            if self.pdf_document:
                self.current_page = position
                self.load_pdf_page()
            else:
                self.text_area.mark_set(tk.INSERT, position)
                self.text_area.see(tk.INSERT)
    def go_to_note(self, event):
        selection = event.widget.curselection()
        if selection:
            note_name = event.widget.get(selection[0])
            note_content = self.annotations[note_name]
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(tk.END, note_content)
    def load_data(self):
        if os.path.exists('ebook_reader_data.pkl'):
            with open('ebook_reader_data.pkl', 'rb') as file:
                data = pickle.load(file)
                self.bookmarks = data.get('bookmarks', {})
                self.annotations = data.get('annotations', {})
                self.reading_history = data.get('reading_history', {})
                self.preferences = data.get('preferences', self.preferences)
        self.update_bookmark_list()
        self.update_notes_list()      
    def add_bookmark(self):
        if not self.current_file:
            self.show_warning_message("Warning", "Please open a file first")
            return
            
        if self.pdf_document:
            position = self.current_page
            context = f"Page {self.current_page + 1}"
        else:
            position = self.text_area.index(tk.INSERT)
            context = self.text_area.get("insert linestart", "insert lineend")
            
        bookmark_name = simpledialog.askstring("Add Bookmark", "Enter bookmark name:", initialvalue=context)
        if bookmark_name:
            self.bookmarks[bookmark_name] = (self.current_file, position)
            self.update_bookmark_list()
            self.save_data()                   
    def update_bookmark_list(self):
        self.bookmark_list.delete(0, tk.END)
        for index, name in enumerate(self.bookmarks, start=1):
            self.bookmark_list.insert(tk.END, f"{index}. {name}")                   
    def go_to_bookmark(self, event):
        selection = event.widget.curselection()
        if selection:
            bookmark_name = event.widget.get(selection[0])
            file_path, position = self.bookmarks[bookmark_name]
            if file_path != self.current_file:
                self.show_info_message("Info", "This bookmark is in another PDF.")
                self.open_file(file_path)
            if self.pdf_document:
                self.current_page = position
                self.load_pdf_page()
            else:
                self.text_area.mark_set(tk.INSERT, position)
                self.text_area.see(tk.INSERT)
    def save_note(self):
        note_content = self.notes_text.get(1.0, tk.END).strip()
        if note_content:
            note_name = simpledialog.askstring("Save Note", "Enter note name:")
            if note_name:
                self.annotations[note_name] = note_content
                self.save_data()
    def export_annotations(self):
        if not self.annotations:
            self.show_info_message("Info", "No annotations to export")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON files", "*.json"), ("All files", "*.*")] )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.annotations, file, indent=4)
            self.show_info_message("Success", "Annotations exported successfully")

    def show_statistics(self):
        total_books = len(self.reading_history)
        total_bookmarks = len(self.bookmarks)
        total_notes = len(self.annotations)
        stats_message = (f"Total books read: {total_books}\n"f"Total bookmarks: {total_bookmarks}\n"f"Total notes: {total_notes}")
        self.show_info_message("Reading Statistics", stats_message)
    def update_reading_history(self):
        if self.current_file:
            self.reading_history[self.current_file] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_data()
    def save_data(self):
        data = {'bookmarks': self.bookmarks,'annotations': self.annotations,'reading_history': self.reading_history, 'preferences': self.preferences}
        with open('ebook_reader_data.pkl', 'wb') as file:
            pickle.dump(data, file)
    def load_data(self):
        if os.path.exists('ebook_reader_data.pkl'):
            with open('ebook_reader_data.pkl', 'rb') as file:
                data = pickle.load(file)
                self.bookmarks = data.get('bookmarks', {})
                self.annotations = data.get('annotations', {})
                self.reading_history = data.get('reading_history', {})
                self.preferences = data.get('preferences', self.preferences)
    def show_recent_files(self):
        recent_files = list(self.reading_history.keys())[-10:]
        recent_files_message = "\n".join(recent_files)
        self.show_info_message("Recent Files", recent_files_message)
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_pdf_page()
    def next_page(self):
        if self.current_page < (self.total_pages - 1):
            self.current_page += 1
            self.load_pdf_page()
    def search_text(self):
        """Enhanced search functionality with options"""
        search_term = self.search_var.get()
        if not search_term:
            return
        if search_term not in self.search_history:
            self.search_history.append(search_term)
            self.search_combo['values'] = list(self.search_history)
        self.search_results.clear()
        self.current_search_index = 0
        case_sensitive = self.case_sensitive_var.get()
        whole_word = self.whole_word_var.get()
        if self.pdf_document:
            self.search_pdf(search_term, case_sensitive, whole_word)
        else:
            self.search_text_document(search_term, case_sensitive, whole_word)
        self.update_search_display()
    def search_pdf(self, search_term, case_sensitive, whole_word):
        """Enhanced PDF search"""
        for page_num in range(self.total_pages):
            page = self.pdf_document[page_num]
            if not case_sensitive:
                search_term = search_term.lower()
            text = page.get_text()
            if not case_sensitive:
                text = text.lower()
            if whole_word:
                pattern = r'\b' + re.escape(search_term) + r'\b'
                matches = re.finditer(pattern, text)
                for match in matches:
                    rect = page.search_for(text[match.start():match.end()])
                    if rect:
                        self.search_results.append((page_num, rect[0]))
            else:
                rect_list = page.search_for(search_term)
                for rect in rect_list:
                    self.search_results.append((page_num, rect))
    def search_text_document(self, search_term, case_sensitive, whole_word):
        """Enhanced text document search"""
        text = self.text_area.get('1.0', tk.END)  
        if not case_sensitive:
            text = text.lower()
            search_term = search_term.lower()      
        if whole_word:
            pattern = r'\b' + re.escape(search_term) + r'\b'
        else:
            pattern = re.escape(search_term)
            
        for match in re.finditer(pattern, text):
            start_index = f"1.0+{match.start()}c"
            end_index = f"1.0+{match.end()}c"
            self.search_results.append((start_index, end_index))
    def update_search_display(self):
        """Update search results display"""
        total_results = len(self.search_results)
        if total_results > 0:
            current_pos = self.current_search_index + 1
            self.result_counter.config(text=f"{current_pos}/{total_results}")
            self.highlight_search_results()
            self.show_search_result()
        else:
            self.result_counter.config(text="0/0")
            self.show_info_message("Search", "No results found")
    def highlight_search_results(self):
        self.text_area.tag_remove('search', '1.0', tk.END)
        for start_pos, end_pos in self.search_results:
            if self.pdf_document:
                continue
            self.text_area.tag_add('search', start_pos, end_pos)
        self.text_area.tag_config('search', background='#FFFFE0', borderwidth=1, relief="solid", bordercolor="red")
    def show_search_result(self):
        if not self.search_results:
            self.show_info_message("Search", "No results found")
            return
        if self.pdf_document:
            page_num, inst = self.search_results[self.current_search_index]
            self.current_page = page_num
            self.load_pdf_page()
            x0, y0, x1, y1 = inst
            self.pdf_canvas.create_rectangle(x0 * self.current_zoom, y0 * self.current_zoom, x1 * self.current_zoom, y1 * self.current_zoom, outline='red', width=2)
            self.pdf_canvas.config(scrollregion=self.pdf_canvas.bbox(tk.ALL))
            self.pdf_canvas.yview_moveto(y0 * self.current_zoom / self.pdf_canvas.bbox(tk.ALL)[3])
            self.pdf_canvas.xview_moveto(x0 * self.current_zoom / self.pdf_canvas.bbox(tk.ALL)[2])
        else:
            start_pos, end_pos = self.search_results[self.current_search_index]
            self.text_area.mark_set(tk.INSERT, start_pos)
            self.text_area.see(tk.INSERT)
            self.text_area.tag_add('current_search', start_pos, end_pos)
            self.text_area.tag_config('current_search', background='#FFFFE0', borderwidth=1, relief="solid", bordercolor="red")
    def prev_search_result(self):
        if self.search_results:
            self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
            self.show_search_result()
    def next_search_result(self):
        if self.search_results:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
            self.show_search_result()
    def load_pdf_page(self):
        if not self.pdf_document:
            return
        self.pdf_canvas.delete("all")
        page = self.pdf_document[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.current_zoom, self.current_zoom))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.current_image = ImageTk.PhotoImage(image=image)
        canvas_width = self.pdf_canvas.winfo_width()
        canvas_height = self.pdf_canvas.winfo_height()
        image_width = self.current_image.width()
        image_height = self.current_image.height()
        x_center = (canvas_width - image_width) // 4
        y_center = (canvas_height - image_height) // 4
        
        self.pdf_canvas.create_image(x_center, y_center, anchor=tk.NW, image=self.current_image)
        self.pdf_canvas.config(scrollregion=self.pdf_canvas.bbox(tk.ALL))
        self.page_var.set(str(self.current_page + 1))
        if self.current_file:
            self.preferences['reading_position'][self.current_file] = self.current_page
    def extract_pdf_toc(self):
        self.toc_tree.delete(*self.toc_tree.get_children())
        toc = self.pdf_document.get_toc()
        def add_toc_item(item, parent=""):
            level, title, page = item
            item_id = self.toc_tree.insert(parent, tk.END, text=title, values=(page,))
            return item_id
        parent_stack = [(0, "")]
        for item in toc:
            level = item[0]
            while parent_stack and parent_stack[-1][0] >= level:
                parent_stack.pop()
            parent_id = parent_stack[-1][1]
            new_id = add_toc_item(item, parent_id)
            parent_stack.append((level, new_id))           
    def go_to_toc_item(self, event):
        selected_item = self.toc_tree.selection()
        if selected_item:
            page_num = self.toc_tree.item(selected_item, 'values')[0]
            self.current_page = int(page_num) - 1
            self.load_pdf_page()        
    def on_pdf_scroll(self, event):
        if event.delta > 0:
            self.prev_page()
        else:
            self.next_page()
    def show_error_message(self, title, message):
        messagebox.showerror(title, message, icon='error')
    def show_warning_message(self, title, message):
        messagebox.showwarning(title, message, icon='warning')
    def show_info_message(self, title, message):
        messagebox.showinfo(title, message, icon='info')
if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"Failed to set DPI awareness: {e}")
    root = tk.Tk()
    app = EbookReader(root)
    root.mainloop()
    app = EbookReader(root)
    root.mainloop()
