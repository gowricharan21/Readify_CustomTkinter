import customtkinter as ctk
import fitz 
from tkinter import filedialog, messagebox, ttk
import os
from docx import Document
from fpdf import FPDF
import json
from PIL import Image, ImageTk
import io
import ctypes
import tkinter as tk 
class EbookReader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Readify")
        self.window.geometry("1200x800")
        self.current_file = None
        self.current_file_path = None
        self.current_page = 0
        self.total_pages = 0
        self.current_image = None
        self.zoom_level = 1.0
        self.current_rotation = 0
        self.bookmarks = {}
        self.search_boxes = []
        self.current_highlight = None
        self.theme = "light"
        self.search_index = -1
        self.search_history = [] 
        self.preferences = {'reading_position': {}}  
        self.pdf_document = None 
        self.original_page_pixmap = None
        self.create_menu_bar()
        self.setup_ui()
        self.load_bookmarks()
        self.setup_key_bindings()
        self.create_context_menu()
        self.create_theme_toggle_button()
        self.create_navigation_buttons()
    def create_theme_toggle_button(self):
        self.theme_toggle_btn = ctk.CTkButton(self.top_frame, text="Change Theme", command=self.toggle_theme)
        self.theme_toggle_btn.pack(side="left", padx=5)
    def toggle_theme(self):
        if self.theme == "light":
            self.theme = "dark"
            ctk.set_appearance_mode("dark")
            self.canvas.config(bg="black")
        else:
            self.theme = "light"
            ctk.set_appearance_mode("light")
            self.canvas.config(bg="white")
        self.display_page()
    def setup_keyboard_shortcuts(self):
        self.root = self.window 
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        # self.root.bind('<Control-b>', lambda e: self.toggle_sidebar())
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
    def focus_search(self):
        """Focus on search entry"""
        self.search_combo.focus_set()
    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=5)
        self.sidebar = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)
        self.bookmark_header = ctk.CTkLabel(self.sidebar, text="📚Bookmarks", font=("Arial", 16, "bold"))
        self.bookmark_header.pack(pady=5)
        self.bookmarks_frame = ctk.CTkScrollableFrame(self.sidebar, width=180, height=600)
        self.bookmarks_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)  
        self.top_frame = ctk.CTkFrame(self.content_frame)
        self.top_frame.pack(fill="x", pady=5)
        self.open_btn = ctk.CTkButton(self.top_frame, text="📂Open ", command=self.open_file)
        self.open_btn.pack(side="left", padx=5)
        self.save_btn = ctk.CTkButton(self.top_frame, text="💾 Save As", command=self.save_as)
        self.save_btn.pack(side="left", padx=5)
        self.bookmark_btn = ctk.CTkButton(self.top_frame, text="Add Bookmark", command=self.add_bookmark_dialog)
        self.bookmark_btn.pack(side="left", padx=5)
        self.zoom_frame = ctk.CTkFrame(self.top_frame)
        self.zoom_frame.pack(side="left", padx=5)        
        self.zoom_out_btn = ctk.CTkButton(self.zoom_frame, text="-", width=30, command=self.zoom_out)
        self.zoom_out_btn.pack(side="left", padx=2)
        self.zoom_label = ctk.CTkLabel(self.zoom_frame, text="100%")
        self.zoom_label.pack(side="left", padx=2)
        self.zoom_in_btn = ctk.CTkButton(self.zoom_frame, text="+", width=30, command=self.zoom_in)
        self.zoom_in_btn.pack(side="left", padx=2)
        self.search_frame = ctk.CTkFrame(self.content_frame)
        self.search_frame.pack(fill="x", pady=5)
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search text...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_btn = ctk.CTkButton(self.search_frame, text="Search 🔍", command=self.search_text)
        self.search_btn.pack(side="left", padx=5)
        self.prev_search_btn = ctk.CTkButton(self.search_frame, text="Previous", command=self.prev_search_result)
        self.prev_search_btn.pack(side="left", padx=5)
        self.next_search_btn = ctk.CTkButton(self.search_frame, text="Next", command=self.next_search_result)
        self.next_search_btn.pack(side="left", padx=5)
        self.clear_search_btn = ctk.CTkButton(self.search_frame, text="Clear Search", command=self.clear_search)
        self.clear_search_btn.pack(side="left", padx=5)
        self.nav_frame = ctk.CTkFrame(self.content_frame)
        self.nav_frame.pack(fill="x", pady=5)
        self.prev_btn = ctk.CTkButton(self.nav_frame, text="◀ Previous", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        self.page_label = ctk.CTkLabel(self.nav_frame, text="Page: 0/0")
        self.page_label.pack(side="left", padx=5)
        self.next_btn = ctk.CTkButton(self.nav_frame, text="Next ▶", command=self.next_page)
        self.next_btn.pack(side="right", padx=5)
        self.canvas_frame = ctk.CTkFrame(self.content_frame)
        self.canvas_frame.pack(fill="both", expand=True, pady=5)
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Motion>", self.check_highlight_hover)
    def zoom_in(self):
        self.zoom_level *= 1.2
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self.display_page()
    def zoom_out(self):
        self.zoom_level /= 1.2
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self.display_page()
    def load_bookmarks(self):
        try:
            if os.path.exists("bookmarks.json"):
                with open("bookmarks.json", "r") as f:
                    self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = {}
    def save_bookmarks(self):
        try:
            with open("bookmarks.json", "w") as f:
                json.dump(self.bookmarks, f)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All supported files", "*.txt *.pdf"),("Text files", "*.txt"),("PDF files", "*.pdf"),("All files", "*.*") ])
        if file_path:
            self.current_file = fitz.open(file_path)
            self.current_file_path = file_path
            self.total_pages = len(self.current_file)
            self.current_page = 0
            self.display_page()
            self.update_bookmarks_display()
    def display_page(self):
        if self.current_file:
            self.canvas.delete("all")
            self.search_boxes = []
            page = self.current_file[self.current_page]
            zoom_matrix = fitz.Matrix(self.zoom_level * 1.5, self.zoom_level * 1.5)
            pix = page.get_pixmap(matrix=zoom_matrix)
            self.original_page_pixmap = pix
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if self.theme == "dark":
                img = Image.eval(img, lambda x: 255 - x) 
            self.current_image = ImageTk.PhotoImage(img)
            self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
            self.canvas.create_image(0, 0, anchor="nw", image=self.current_image)
            self.page_label.configure(text=f"Page: {self.current_page + 1}/{self.total_pages}")
    def search_text(self):
        if not self.current_file:
            return  
        search_term = self.search_entry.get()
        if not search_term:
            return
        self.canvas.delete("highlight")
        self.search_boxes = []
        page = self.current_file[self.current_page]
        text_instances = page.search_for(search_term)
        zoom_matrix = fitz.Matrix(self.zoom_level * 1.5, self.zoom_level * 1.5)
        for inst in text_instances:
            x0, y0, x1, y1 = [coord * self.zoom_level * 1.5 for coord in inst]
            highlight = self.canvas.create_rectangle( x0, y0, x1, y1,fill="yellow", stipple="gray50", outline="",tags="highlight" )
            self.search_boxes.append({ "bbox": (x0, y0, x1, y1),"id": highlight })
        self.search_index = -1
    def next_search_result(self):
        if self.search_boxes:
            self.search_index = (self.search_index + 1) % len(self.search_boxes)
            self.highlight_search_result()
    def prev_search_result(self):
        if self.search_boxes:
            self.search_index = (self.search_index - 1) % len(self.search_boxes)
            self.highlight_search_result()
    def highlight_search_result(self):
        if self.search_boxes and 0 <= self.search_index < len(self.search_boxes):
            box = self.search_boxes[self.search_index]
            self.canvas.yview_moveto(box["bbox"][1] / self.canvas.bbox("all")[3])
            self.canvas.itemconfig(box["id"], outline="blue", width=2)
            if self.current_highlight and self.current_highlight != box["id"]:
                self.canvas.itemconfig(self.current_highlight, outline="")
            self.current_highlight = box["id"]    
    def check_highlight_hover(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for box in self.search_boxes:
            x0, y0, x1, y1 = box["bbox"]
            if x0 <= x <= x1 and y0 <= y <= y1:
                if self.current_highlight != box["id"]:
                    if self.current_highlight:
                        self.canvas.itemconfig(self.current_highlight, outline="")
                    self.canvas.itemconfig(box["id"], outline="red", width=2)
                    self.current_highlight = box["id"]
                return
        if self.current_highlight:
            self.canvas.itemconfig(self.current_highlight, outline="")
            self.current_highlight = None
    def add_bookmark_dialog(self):
        if not self.current_file:
            messagebox.showerror("Error", "No file is currently open")
            return          
        dialog = ctk.CTkInputDialog(text="Enter bookmark title:",title="Add Bookmark")
        bookmark_title = dialog.get_input()
        if bookmark_title:
            self.add_bookmark(bookmark_title)
    def add_bookmark(self, title):
        if self.current_file_path not in self.bookmarks:
            self.bookmarks[self.current_file_path] = {}
        self.bookmarks[self.current_file_path][str(self.current_page)] = {"title": title, "timestamp": str(os.path.getmtime(self.current_file_path)) }
        self.save_bookmarks()
        self.update_bookmarks_display()
    def update_bookmarks_display(self):
        for widget in self.bookmarks_frame.winfo_children():
            widget.destroy()
        if self.current_file_path in self.bookmarks:
            for page, bookmark_data in self.bookmarks[self.current_file_path].items():
                bookmark_frame = ctk.CTkFrame(self.bookmarks_frame)
                bookmark_frame.pack(fill="x", pady=2)
                bookmark_button = ctk.CTkButton(bookmark_frame,text=f"{bookmark_data['title']} (Page {int(page)+1})",command=lambda p=int(page): self.goto_page(p) )
                bookmark_button.pack(side="left", padx=2, fill="x", expand=True)
                delete_button = ctk.CTkButton( bookmark_frame,text="×",width=30,command=lambda p=page: self.delete_bookmark(p))
                delete_button.pack(side="right", padx=2)
    def delete_bookmark(self, page):
        if self.current_file_path in self.bookmarks:
            if str(page) in self.bookmarks[self.current_file_path]:
                del self.bookmarks[self.current_file_path][str(page)]
                self.save_bookmarks()
                self.update_bookmarks_display()
    def goto_page(self, page_number):
        if self.current_file and 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self.display_page()
    def next_page(self):
        if self.current_file and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
    def prev_page(self):
        if self.current_file and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    def save_as(self):
        if not self.current_file:
            messagebox.showerror("Error", "No file is currently open")
            return
        file_types = [("PNG Image", "*.png"),("JPEG Image", "*.jpg"),("PDF files", "*.pdf"),("Text files", "*.txt"), ("Word files", "*.docx") ]
        save_path = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=".pdf")
        if save_path:
            ext = os.path.splitext(save_path)[1].lower()
            page = self.current_file[self.current_page]
            text = page.get_text()
            if ext == ".txt":
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)
            elif ext == ".docx":
                doc = Document()
                doc.add_paragraph(text)
                doc.save(save_path)
            elif ext == '.pdf':
                output_pdf = fitz.open()
                output_pdf.insert_pdf(self.current_file, from_page=self.current_page, to_page=self.current_page)
                output_pdf.save(save_path)
                output_pdf.close()
            elif ext in ['.png', '.jpg']:
                pil_image = Image.frombytes(
                    "RGB",
                    [self.original_page_pixmap.width, self.original_page_pixmap.height],
                    self.original_page_pixmap.samples
                )
                pil_image.save(save_path)
    def handle_mousewheel(self, event):
        if event.state & 4:
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")        
    def setup_key_bindings(self):
        self.window.bind("<Control-o>", lambda e: self.open_file())
        self.window.bind("<Control-s>", lambda e: self.save_as())
        self.window.bind("<Control-b>", lambda e: self.add_bookmark_dialog())
        self.window.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.window.bind("<Left>", lambda e: self.prev_page())
        self.window.bind("<Right>", lambda e: self.next_page())
        self.window.bind("<Control-plus>", lambda e: self.zoom_in())
        self.window.bind("<Control-minus>", lambda e: self.zoom_out())
        self.window.bind("<Control-MouseWheel>", self.handle_mousewheel)
        self.window.bind("<Control-Home>", lambda e: self.first_page())
        self.window.bind("<Control-End>", lambda e: self.last_page())     
    def create_context_menu(self):
        self.context_menu = ctk.CTkFrame(self.window)
        menu_items = [ ("Add Bookmark", self.add_bookmark_dialog),("Copy Text", self.copy_selected_text), ("Save Page As", self.save_as),("Search on Page", lambda: self.search_entry.focus_set())]
        for text, command in menu_items:
            btn = ctk.CTkButton(self.context_menu, text=text, command=command)
            btn.pack(fill="x", padx=2, pady=1)
            
        self.canvas.bind("<Button-3>", self.show_context_menu)       
    def show_context_menu(self, event):
        if self.current_file:
            self.context_menu.place(x=event.x_root, y=event.y_root)
            self.window.bind("<Button-1>", lambda e: self.hide_context_menu())           
    def hide_context_menu(self):
        self.context_menu.place_forget()
        self.window.unbind("<Button-1>")       
    def copy_selected_text(self):
        if self.current_file:
            page = self.current_file[self.current_page]
            text = page.get_text()
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
    def rotate_page(self, angle=90):
        if self.current_file:
            self.current_rotation = (self.current_rotation + angle) % 360
            self.display_page()       
    def export_bookmarks(self):
        if not self.bookmarks:
            messagebox.showinfo("Info", "No bookmarks to export")
            return   
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.bookmarks, f, indent=4)
                messagebox.showinfo("Success", "Bookmarks exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting bookmarks: {str(e)}")               
    def import_bookmarks(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_bookmarks = json.load(f)
                for file_path, bookmarks in imported_bookmarks.items():
                    if file_path not in self.bookmarks:
                        self.bookmarks[file_path] = {}
                    self.bookmarks[file_path].update(bookmarks)
                    
                self.save_bookmarks()
                self.update_bookmarks_display()
                messagebox.showinfo("Success", "Bookmarks imported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error importing bookmarks: {str(e)}")
                
    def create_menu_bar(self):
        menu_bar = ctk.CTkFrame(self.window)
        menu_bar.pack(fill="x", padx=5, pady=2)
        file_menu = ctk.CTkFrame(menu_bar)
        file_menu.pack(side="left", padx=5)
        ctk.CTkButton(file_menu, text="File", width=60, command=self.show_file_menu).pack()
        view_menu = ctk.CTkFrame(menu_bar)
        view_menu.pack(side="left", padx=5)
        ctk.CTkButton(view_menu, text="View", width=60, command=self.show_view_menu).pack()
        bookmarks_menu = ctk.CTkFrame(menu_bar)
        bookmarks_menu.pack(side="left", padx=5)
        ctk.CTkButton(bookmarks_menu, text="Bookmarks", width=80, command=self.show_bookmarks_menu).pack()
        
    def show_file_menu(self):
        menu = ctk.CTkFrame(self.window)
        menu_items = [ ("Open", self.open_file),("Save As", self.save_as), ("Export Bookmarks", self.export_bookmarks),("Import Bookmarks", self.import_bookmarks),("Exit", self.window.quit)]
        self.create_dropdown_menu(menu, menu_items)
        
    def show_view_menu(self):
        menu = ctk.CTkFrame(self.window)
        menu_items = [  ("Zoom In", self.zoom_in), ("Zoom Out", self.zoom_out), ("Rotate Right", lambda: self.rotate_page(90)), ("Rotate Left", lambda: self.rotate_page(-90))]
        self.create_dropdown_menu(menu, menu_items)
    def show_bookmarks_menu(self):
        menu = ctk.CTkFrame(self.window)
        menu_items = [ ("Add Bookmark", self.add_bookmark_dialog),("Export Bookmarks", self.export_bookmarks),("Import Bookmarks", self.import_bookmarks) ]
        self.create_dropdown_menu(menu, menu_items)
        
    def create_dropdown_menu(self, menu, items):
        x = self.window.winfo_pointerx() - self.window.winfo_rootx()
        y = self.window.winfo_pointery() - self.window.winfo_rooty()
        menu.place(x=x, y=y)
        for text, command in items:
            btn = ctk.CTkButton(menu, text=text, command=lambda c=command: self.handle_menu_click(menu, c))
            btn.pack(fill="x", padx=2, pady=1)
        self.window.bind("<Button-1>", lambda e: self.hide_dropdown_menu(menu))
        
    def handle_menu_click(self, menu, command):
        menu.place_forget()
        command()
        
    def hide_dropdown_menu(self, menu):
        menu.place_forget()
        self.window.unbind("<Button-1>")      
    def create_navigation_buttons(self):
        self.first_page_btn = ctk.CTkButton(self.nav_frame, text="⏮First Page", command=self.first_page)
        self.first_page_btn.pack(side="left", padx=5)
        self.last_page_btn = ctk.CTkButton(self.nav_frame, text="⏭Last Page", command=self.last_page)
        self.last_page_btn.pack(side="right", padx=5)
    def first_page(self):
        if self.current_file:
            self.current_page = 0
            self.display_page()
    def last_page(self):
        if self.current_file:
            self.current_page = self.total_pages - 1
            self.display_page()
    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.canvas.delete("highlight")
        self.search_boxes = []
        self.search_index = -1      
    def run(self):
        self.window.mainloop()
if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"Failed to set DPI awareness: {e}")
    app = EbookReader()
    app.run()
