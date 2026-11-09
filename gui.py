"""
gui.py
Two-Page Interactive Graphical User Interface (GUI) for Digital Junk Drawer.

Workflow:
Page 1 - Ingestion & Unorganized Inbox:
  1. Detects and displays all files in 'sample_unorganized_files'.
  2. Allows users to add files via file picker or directly place them into the folder.
  3. "Proceed to Arrange into Organised Folders": runs ML classification, arranges files
     into major category folders, indexes them in Custom HashMap and FolderTree.
  4. "View Organised Folders (New Page) ➔": Transitions to the interactive exploration page.

Page 2 - Organised Folders Explorer:
  1. Interactive folder cards (Business, Tech, Politics, Sports, Entertainment).
  2. Search bar for folders that retrieves folder properties + polynomial Hash-Code.
  3. Interactive folder click: opens and displays files within the selected folder.
  4. Custom Merge Sort controls:
     - Sort by: Filename, Date of Upload, File Size
     - Order: Ascending (A-Z / Min / Old) or Descending (Z-A / Max / New)
  5. File table displaying Doc ID, Name, Size, Upload Date, and Document Hash-Code.
  6. Live HashMap diagnostic stats.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from dsa.document import Document
from document_manager import DocumentManager
from security_manager import vault_manager


class DigitalJunkDrawerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Digital Junk Drawer — ML Document Classifier & DSA Organizer")
        self.root.geometry("1220x800")
        self.root.minsize(1020, 680)

        # Paths
        self.unorganized_dir = os.path.abspath("sample_unorganized_files")
        self.organized_dir = os.path.abspath("organized_files_output")

        # Ensure directories exist
        os.makedirs(self.unorganized_dir, exist_ok=True)
        os.makedirs(self.organized_dir, exist_ok=True)

        # Initialize DocumentManager
        self.manager = DocumentManager()
        self.manager.sync_with_disk(self.organized_dir, auto_discover=True)

        # State tracking
        self.current_folder_selected: str = "All Folders"
        self.last_organized_count: int = 0

        # Setup styling
        self._setup_styles()

        # Main container with page frames
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Build Pages
        self.page1 = ttk.Frame(self.main_container)
        self.page2 = ttk.Frame(self.main_container)

        self._build_page1_unorganized()
        self._build_page2_organized()

        # Start on Page 1
        self.show_page1()

        # Initial scan of unorganized files
        self.refresh_unorganized_table()

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.bg_color = "#f1f5f9"
        self.card_bg = "#ffffff"
        self.primary_blue = "#2563eb"
        self.success_green = "#16a34a"
        self.accent_purple = "#7c3aed"
        self.dark_header = "#0f172a"

        self.root.configure(bg=self.bg_color)
        self.style.configure(".", background=self.bg_color, font=("Segoe UI", 9))

        # Frames
        self.style.configure("Header.TFrame", background=self.dark_header)
        self.style.configure("Card.TFrame", background=self.card_bg, relief="solid", borderwidth=1)
        self.style.configure("Banner.TFrame", background="#e2e8f0")

        # Labels
        self.style.configure("HeaderTitle.TLabel", background=self.dark_header, foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        self.style.configure("HeaderSub.TLabel", background=self.dark_header, foreground="#94a3b8", font=("Segoe UI", 9))
        self.style.configure("CardTitle.TLabel", background=self.card_bg, foreground="#0f172a", font=("Segoe UI", 11, "bold"))
        self.style.configure("CardProp.TLabel", background=self.card_bg, foreground="#334155", font=("Segoe UI", 9))
        self.style.configure("CardPropBold.TLabel", background=self.card_bg, foreground="#0f172a", font=("Segoe UI", 9, "bold"))

        # Buttons
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.configure("Nav.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.configure("Action.TButton", font=("Segoe UI", 9), padding=5)

        # Treeview / Tables
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # =========================================================================
    # PAGE NAVIGATION
    # =========================================================================

    def show_page1(self):
        """Shows Page 1: Unorganized Files Inbox."""
        self.page2.pack_forget()
        self.page1.pack(fill=tk.BOTH, expand=True)
        self.refresh_unorganized_table()

    def show_page2(self):
        """Shows Page 2: Organized Folders Explorer (Protected by Cryptographic Vault Lock)."""
        if not self.is_vault_unlocked:
            pwd = simpledialog.askstring(
                "🔐 Folder Vault Security Lock",
                "Enter Password to generate hashcode and unlock organized folders:\n(Master Password: Ron567)",
                show="*",
                parent=self.root
            )
            if not pwd:
                return

            res = vault_manager.verify_password(pwd)
            if res["matched"]:
                self.is_vault_unlocked = True
                messagebox.showinfo(
                    "✓ Access Granted",
                    f"✓ Hashcode matched perfectly!\n\nInput SHA-256:\n{res['input_hash'][:32]}...\n\nStored Vault Hashcode:\n{res['stored_hash'][:32]}...\n\nLocation: security_vault.json\nAccess authorized to Organised Folders!",
                    parent=self.root
                )
            else:
                messagebox.showerror(
                    "❌ Access Denied",
                    f"❌ Try again, hashcode didn't match!\n\nInput SHA-256:\n{res['input_hash']}\n\nStored Vault Hashcode:\n{res['stored_hash']}\n\nLocation: security_vault.json",
                    parent=self.root
                )
                return

        self.page1.pack_forget()
        self.page2.pack(fill=tk.BOTH, expand=True)
        self.manager.sync_with_disk(self.organized_dir, auto_discover=True)
        self.refresh_folder_cards()
        self.select_folder_category("All Folders")

    # =========================================================================
    # PAGE 1: UNORGANIZED INBOX
    # =========================================================================

    def _build_page1_unorganized(self):
        # 1. Top Header
        header = ttk.Frame(self.page1, style="Header.TFrame", padding=(16, 12))
        header.pack(fill=tk.X)

        title_box = ttk.Frame(header, style="Header.TFrame")
        title_box.pack(side=tk.LEFT)

        ttk.Label(title_box, text="📥 Stage 1: Unorganized Files Inbox", style="HeaderTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_box,
            text="Place files into 'sample_unorganized_files' directly or via button, then click Proceed to Arrange.",
            style="HeaderSub.TLabel"
        ).pack(anchor=tk.W, pady=(2, 0))

        # Launch Web UI Button in Header
        web_btn_box = ttk.Frame(header, style="Header.TFrame")
        web_btn_box.pack(side=tk.RIGHT)

        ttk.Button(
            web_btn_box,
            text="🌐 Launch Web UI (HTML/CSS/JS)",
            command=self.launch_web_ui,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=4)

        # 2. Folder Actions Banner
        action_card = ttk.Frame(self.page1, style="Card.TFrame", padding=12)
        action_card.pack(fill=tk.X, padx=14, pady=(12, 6))

        btn_row = ttk.Frame(action_card, style="Card.TFrame")
        btn_row.pack(fill=tk.X)

        ttk.Button(
            btn_row,
            text="➕ Upload / Add Files to Inbox",
            command=self.upload_files_to_unorganized,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_row,
            text="📁 Open 'sample_unorganized_files' in Explorer",
            command=lambda: self.open_in_explorer(self.unorganized_dir),
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_row,
            text="🔄 Refresh Inbox Table",
            command=self.refresh_unorganized_table,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        self.lbl_unorganized_count = ttk.Label(
            btn_row,
            text="Found: 0 items",
            style="CardPropBold.TLabel",
            foreground="#1e40af"
        )
        self.lbl_unorganized_count.pack(side=tk.RIGHT, padx=6)

        # 3. Unorganized Files Table
        table_card = ttk.Frame(self.page1, style="Card.TFrame", padding=10)
        table_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        ttk.Label(
            table_card,
            text="Files Waiting to be Organized (inside sample_unorganized_files/):",
            style="CardTitle.TLabel"
        ).pack(anchor=tk.W, pady=(0, 6))

        tbl_container = ttk.Frame(table_card)
        tbl_container.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tbl_container)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        cols = ("name", "type", "size", "modified", "path")
        self.unorganized_table = ttk.Treeview(
            tbl_container,
            columns=cols,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="extended"
        )
        scroll_y.config(command=self.unorganized_table.yview)

        self.unorganized_table.heading("name", text="Filename / Item Name")
        self.unorganized_table.heading("type", text="Type")
        self.unorganized_table.heading("size", text="Size")
        self.unorganized_table.heading("modified", text="Date Modified")
        self.unorganized_table.heading("path", text="Absolute Path")

        self.unorganized_table.column("name", width=340, anchor=tk.W)
        self.unorganized_table.column("type", width=90, anchor=tk.CENTER)
        self.unorganized_table.column("size", width=110, anchor=tk.E)
        self.unorganized_table.column("modified", width=160, anchor=tk.CENTER)
        self.unorganized_table.column("path", width=420, anchor=tk.W)

        self.unorganized_table.pack(fill=tk.BOTH, expand=True)
        self.unorganized_table.bind("<Button-3>", self.show_unorg_table_context_menu)

        # Context Menu for unorganized_table
        self.unorg_context_menu = tk.Menu(self.root, tearoff=0)
        self.unorg_context_menu.add_command(
            label="📋 Copy Filename", command=self.copy_selected_unorg_filename
        )

        # 4. Bottom Execution Card
        exec_card = ttk.Frame(self.page1, style="Card.TFrame", padding=14)
        exec_card.pack(fill=tk.X, padx=14, pady=(6, 14))

        exec_box = ttk.Frame(exec_card, style="Card.TFrame")
        exec_box.pack(fill=tk.X)

        self.btn_proceed_arrange = ttk.Button(
            exec_box,
            text="⚡ Proceed to Arrange into Organised Folders",
            command=self.proceed_to_arrange_files,
            style="Success.TButton"
        )
        self.btn_proceed_arrange.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_view_organized = ttk.Button(
            exec_box,
            text="📂 View Organised Folders (New Page) ➔",
            command=self.show_page2,
            style="Nav.TButton"
        )
        self.btn_view_organized.pack(side=tk.LEFT)

        self.lbl_p1_status = ttk.Label(
            exec_box,
            text="Ready. Click 'Proceed to Arrange' to categorize using ML & organize files.",
            style="CardProp.TLabel",
            font=("Segoe UI", 9, "italic")
        )
        self.lbl_p1_status.pack(side=tk.RIGHT, padx=6)

    # =========================================================================
    # PAGE 2: ORGANISED FOLDERS EXPLORER
    # =========================================================================

    def _build_page2_organized(self):
        # 1. Top Header
        header = ttk.Frame(self.page2, style="Header.TFrame", padding=(16, 12))
        header.pack(fill=tk.X)

        title_box = ttk.Frame(header, style="Header.TFrame")
        title_box.pack(side=tk.LEFT)

        ttk.Label(title_box, text="📂 Stage 2: Organised Folders Explorer", style="HeaderTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_box,
            text="Search folders by name to inspect properties & Hash-Codes, click folders to open, and run Merge Sort.",
            style="HeaderSub.TLabel"
        ).pack(anchor=tk.W, pady=(2, 0))

        nav_box = ttk.Frame(header, style="Header.TFrame")
        nav_box.pack(side=tk.RIGHT)

        ttk.Button(
            nav_box,
            text="⬅ Back to Unorganized Inbox",
            command=self.show_page1,
            style="Action.TButton"
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Button(
            nav_box,
            text="🔄 Resync Disk Files",
            command=self.resync_disk_files,
            style="Action.TButton"
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Button(
            nav_box,
            text="🌐 Launch Web UI (HTML/CSS/JS)",
            command=self.launch_web_ui,
            style="Primary.TButton"
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Button(
            nav_box,
            text="📁 Open Root Folder in Explorer",
            command=lambda: self.open_in_explorer(self.organized_dir),
            style="Action.TButton"
        ).pack(side=tk.RIGHT, padx=4)

        # 2. Search & Properties Panel
        search_card = ttk.Frame(self.page2, style="Card.TFrame", padding=12)
        search_card.pack(fill=tk.X, padx=14, pady=(10, 4))

        # Row 1: Folder Search
        search_row = ttk.Frame(search_card, style="Card.TFrame")
        search_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(
            search_row,
            text="📁 Search Folder Name:",
            font=("Segoe UI", 10, "bold"),
            background=self.card_bg
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.entry_folder_search = ttk.Entry(search_row, width=28, font=("Segoe UI", 10))
        self.entry_folder_search.pack(side=tk.LEFT, padx=4)
        self.entry_folder_search.bind("<KeyRelease>", lambda e: self.handle_folder_search())
        self.entry_folder_search.bind("<Return>", lambda e: self.handle_folder_search())

        ttk.Button(
            search_row,
            text="Search Folder",
            command=self.handle_folder_search,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            search_row,
            text="Reset Folder",
            command=self.reset_folder_search,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        # Row 2: File Search
        file_search_row = ttk.Frame(search_card, style="Card.TFrame")
        file_search_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            file_search_row,
            text="🔍 Search Files (Any Folder):",
            font=("Segoe UI", 10, "bold"),
            background=self.card_bg
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.entry_file_search = ttk.Entry(file_search_row, width=38, font=("Segoe UI", 10))
        self.entry_file_search.pack(side=tk.LEFT, padx=4)
        self.entry_file_search.bind("<KeyRelease>", lambda e: self.handle_file_live_search())

        ttk.Button(
            file_search_row,
            text="Clear Search",
            command=self.clear_file_search,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        # Folder Properties Card (Displays Name, Hash-Code, Size, Breakdown)
        self.props_frame = ttk.Frame(search_card, style="Card.TFrame", relief="solid", borderwidth=1, padding=10)
        self.props_frame.pack(fill=tk.X, pady=(4, 0))

        self.lbl_folder_title = ttk.Label(
            self.props_frame,
            text="📁 Folder: All Organised Folders",
            font=("Segoe UI", 12, "bold"),
            foreground="#0f172a",
            background=self.card_bg
        )
        self.lbl_folder_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        ttk.Button(
            self.props_frame,
            text="🌳 Visualise Folder Tree",
            command=lambda: self.open_tree_visualizer(self.current_folder_selected),
            style="Primary.TButton"
        ).grid(row=0, column=2, columnspan=2, sticky=tk.E, pady=(0, 6), padx=4)

        # Properties Grid
        ttk.Label(self.props_frame, text="🔑 Folder Hash-Code:", style="CardPropBold.TLabel").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
        self.lbl_prop_hash = ttk.Label(self.props_frame, text="N/A", style="CardProp.TLabel", foreground="#7c3aed", font=("Segoe UI", 9, "bold"))
        self.lbl_prop_hash.grid(row=1, column=1, sticky=tk.W, padx=4, pady=2)

        ttk.Label(self.props_frame, text="📊 Total Files Count:", style="CardPropBold.TLabel").grid(row=2, column=0, sticky=tk.W, padx=4, pady=2)
        self.lbl_prop_count = ttk.Label(self.props_frame, text="0 files", style="CardProp.TLabel")
        self.lbl_prop_count.grid(row=2, column=1, sticky=tk.W, padx=4, pady=2)

        ttk.Label(self.props_frame, text="💾 Total Folder Size:", style="CardPropBold.TLabel").grid(row=1, column=2, sticky=tk.W, padx=(20, 4), pady=2)
        self.lbl_prop_size = ttk.Label(self.props_frame, text="0 B", style="CardProp.TLabel")
        self.lbl_prop_size.grid(row=1, column=3, sticky=tk.W, padx=4, pady=2)

        ttk.Label(self.props_frame, text="📑 File Types Breakdown:", style="CardPropBold.TLabel").grid(row=2, column=2, sticky=tk.W, padx=(20, 4), pady=2)
        self.lbl_prop_types = ttk.Label(self.props_frame, text="None", style="CardProp.TLabel")
        self.lbl_prop_types.grid(row=2, column=3, sticky=tk.W, padx=4, pady=2)

        ttk.Label(self.props_frame, text="📍 Folder Path:", style="CardPropBold.TLabel").grid(row=3, column=0, sticky=tk.W, padx=4, pady=2)
        self.lbl_prop_path = ttk.Label(self.props_frame, text=self.organized_dir, style="CardProp.TLabel", foreground="#64748b")
        self.lbl_prop_path.grid(row=3, column=1, columnspan=3, sticky=tk.W, padx=4, pady=2)

        # 3. Interactive Folder Cards Selector
        folders_bar = ttk.Frame(self.page2, style="Card.TFrame", padding=(12, 8))
        folders_bar.pack(fill=tk.X, padx=14, pady=4)

        ttk.Label(
            folders_bar,
            text="Interactive Folders (Click any folder to open and explore its files):",
            font=("Segoe UI", 9, "bold"),
            background=self.card_bg
        ).pack(anchor=tk.W, pady=(0, 6))

        self.cards_container = ttk.Frame(folders_bar, style="Card.TFrame")
        self.cards_container.pack(fill=tk.X)

        # 4. Sorting & Controls Bar
        sort_card = ttk.Frame(self.page2, style="Card.TFrame", padding=(12, 8))
        sort_card.pack(fill=tk.X, padx=14, pady=4)

        sort_row = ttk.Frame(sort_card, style="Card.TFrame")
        sort_row.pack(fill=tk.X)

        ttk.Label(sort_row, text="⚡ Custom Merge Sort Controls:", font=("Segoe UI", 9, "bold"), background=self.card_bg).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(sort_row, text="Sort By:", background=self.card_bg).pack(side=tk.LEFT, padx=(6, 2))
        self.combo_sort_key = ttk.Combobox(
            sort_row,
            values=["Filename", "Date of Upload", "File Size"],
            state="readonly",
            width=16
        )
        self.combo_sort_key.current(0)
        self.combo_sort_key.pack(side=tk.LEFT, padx=4)

        ttk.Label(sort_row, text="Order:", background=self.card_bg).pack(side=tk.LEFT, padx=(10, 2))
        self.combo_sort_order = ttk.Combobox(
            sort_row,
            values=["Ascending (A-Z / Min / Old)", "Descending (Z-A / Max / New)"],
            state="readonly",
            width=24
        )
        self.combo_sort_order.current(0)
        self.combo_sort_order.pack(side=tk.LEFT, padx=4)

        ttk.Button(
            sort_row,
            text="Sort Files (Merge Sort)",
            command=self.handle_merge_sort,
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=(12, 4))

        self.lbl_sort_feedback = ttk.Label(
            sort_row,
            text="Showing all documents.",
            background=self.card_bg,
            font=("Segoe UI", 9, "italic")
        )
        self.lbl_sort_feedback.pack(side=tk.RIGHT, padx=4)

        # 5. Organised Documents Table
        files_card = ttk.Frame(self.page2, style="Card.TFrame", padding=10)
        files_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 10))

        self.lbl_table_header = ttk.Label(
            files_card,
            text="Files Inside: All Folders",
            style="CardTitle.TLabel"
        )
        self.lbl_table_header.pack(anchor=tk.W, pady=(0, 6))

        tbl_box = ttk.Frame(files_card)
        tbl_box.pack(fill=tk.BOTH, expand=True)

        scr_y = ttk.Scrollbar(tbl_box)
        scr_y.pack(side=tk.RIGHT, fill=tk.Y)

        scr_x = ttk.Scrollbar(tbl_box, orient=tk.HORIZONTAL)
        scr_x.pack(side=tk.BOTTOM, fill=tk.X)

        doc_cols = ("doc_id", "filename", "category", "size", "type", "upload_time", "hash_code")
        self.doc_table = ttk.Treeview(
            tbl_box,
            columns=doc_cols,
            show="headings",
            yscrollcommand=scr_y.set,
            xscrollcommand=scr_x.set,
            selectmode="browse"
        )
        scr_y.config(command=self.doc_table.yview)
        scr_x.config(command=self.doc_table.xview)

        self.doc_table.heading("doc_id", text="Doc ID")
        self.doc_table.heading("filename", text="Filename")
        self.doc_table.heading("category", text="Folder / Category")
        self.doc_table.heading("size", text="File Size")
        self.doc_table.heading("type", text="Type")
        self.doc_table.heading("upload_time", text="Upload Date")
        self.doc_table.heading("hash_code", text="Document Hash-Code")

        self.doc_table.column("doc_id", width=95, anchor=tk.CENTER)
        self.doc_table.column("filename", width=310, anchor=tk.W)
        self.doc_table.column("category", width=120, anchor=tk.CENTER)
        self.doc_table.column("size", width=105, anchor=tk.E)
        self.doc_table.column("type", width=70, anchor=tk.CENTER)
        self.doc_table.column("upload_time", width=155, anchor=tk.CENTER)
        self.doc_table.column("hash_code", width=160, anchor=tk.CENTER)

        self.doc_table.pack(fill=tk.BOTH, expand=True)
        self.doc_table.bind("<Double-1>", lambda e: self.show_doc_details())
        self.doc_table.bind("<Button-3>", self.show_doc_table_context_menu)

        # Context Menu for doc_table
        self.doc_context_menu = tk.Menu(self.root, tearoff=0)
        self.doc_context_menu.add_command(
            label="📋 Copy Filename", command=self.copy_selected_doc_filename
        )
        self.doc_context_menu.add_command(
            label="🆔 Copy Document ID", command=self.copy_selected_doc_id
        )
        self.doc_context_menu.add_command(
            label="🔑 Copy Hash-Code", command=self.copy_selected_doc_hash
        )
        self.doc_context_menu.add_separator()
        self.doc_context_menu.add_command(
            label="ℹ️ View Full Properties", command=self.show_doc_details
        )

        # Bottom Bar: HashMap Diagnostics
        bottom_bar = ttk.Frame(self.page2, style="Banner.TFrame", padding=(14, 6))
        bottom_bar.pack(fill=tk.X)

        self.lbl_p2_diagnostics = ttk.Label(
            bottom_bar,
            text="Custom HashMap: Size(N)=0 | Capacity(M)=16 | Load=0.00 | Collisions=0",
            font=("Segoe UI", 9, "bold"),
            foreground="#1e3a8a",
            background="#e2e8f0"
        )
        self.lbl_p2_diagnostics.pack(side=tk.LEFT)

    # =========================================================================
    # LOGIC & EVENT HANDLERS
    # =========================================================================

    def refresh_unorganized_table(self):
        """Scans sample_unorganized_files and updates Page 1 table."""
        for row in self.unorganized_table.get_children():
            self.unorganized_table.delete(row)

        items = self.manager.scan_unorganized_folder(self.unorganized_dir)
        for item in items:
            self.unorganized_table.insert(
                "",
                "end",
                values=(
                    item["name"],
                    item["file_type"],
                    item["formatted_size"],
                    item["modified_time"],
                    item["path"]
                )
            )

        self.lbl_unorganized_count.config(text=f"Found: {len(items)} items in sample_unorganized_files/")
        self.lbl_p1_status.config(text=f"Inbox updated. {len(items)} items ready for arrangement.")

    def upload_files_to_unorganized(self):
        """Allows user to pick files from computer to copy into sample_unorganized_files."""
        file_paths = filedialog.askopenfilenames(
            title="Select Files to Add to sample_unorganized_files",
            filetypes=[
                ("All Supported Files", "*.pdf;*.docx;*.xlsx;*.csv;*.txt;*.mp4;*.zip;*.mkv;*.py;*.mp3"),
                ("All Files", "*.*")
            ]
        )
        if file_paths:
            added = 0
            for src in file_paths:
                dest = os.path.join(self.unorganized_dir, os.path.basename(src))
                shutil.copy2(src, dest)
                added += 1

            self.refresh_unorganized_table()
            messagebox.showinfo(
                "Files Added",
                f"Successfully added {added} file(s) into:\n{self.unorganized_dir}"
            )

    def proceed_to_arrange_files(self):
        """
        Processes all files in sample_unorganized_files:
        1. Predicts category via ML model.
        2. Copies files into organized_files_output/<category>/.
        3. Indexes in Custom HashMap and FolderTree.
        """
        items = self.manager.scan_unorganized_folder(self.unorganized_dir)
        if not items:
            messagebox.showwarning(
                "Inbox Empty",
                "No files found in 'sample_unorganized_files'.\nPlease add some files first!"
            )
            return

        # Execute batch arrangement
        results = self.manager.organize_from_unorganized_folder(
            source_dir=self.unorganized_dir,
            target_dir=self.organized_dir,
            action="copy",
            clean_target=True
        )

        self.last_organized_count = len(results)
        self.is_vault_unlocked = False
        vault_manager.lock()

        self.lbl_p1_status.config(
            text=f"✓ Arranged {len(results)} items into '{self.organized_dir}'! (Vault Locked)"
        )

        # Notify user with full breakdown
        summary_msg = f"Successfully classified and arranged {len(results)} items!\n\n"
        for r in results[:6]:
            summary_msg += f"• {r['filename'][:35]} -> 📂 {r['category']} ({r['confidence']:.1f}%)\n"
        if len(results) > 6:
            summary_msg += f"• ... and {len(results) - 6} more items.\n"

        summary_msg += "\n🔐 Organised folders are locked!\nClick 'View Organised Folders (New Page) ➔' and enter password 'Ron567' to unlock."

        messagebox.showinfo("Arrangement Complete & Locked", summary_msg)

    def resync_disk_files(self):
        """Forces immediate re-synchronization with disk files in organized_files_output."""
        count = self.manager.sync_with_disk(self.organized_dir, auto_discover=True)
        self.refresh_folder_cards()
        self.select_folder_category(self.current_folder_selected)
        messagebox.showinfo(
            "Disk Synchronized",
            f"Successfully synchronized with disk files!\n{count} active documents found in '{self.organized_dir}'."
        )

    def refresh_folder_cards(self):
        """Re-creates interactive clickable cards for each folder on Page 2."""
        for child in self.cards_container.winfo_children():
            child.destroy()

        self.manager.sync_with_disk(self.organized_dir)
        categories = ["All Folders"] + self.manager.tree.get_categories()

        for cat in categories:
            if cat == "All Folders":
                count = len(self.manager.list_all_documents(sync_disk=False))
            else:
                count = len(self.manager.list_documents_in_category(cat, sync_disk=False))

            card_frame = tk.Frame(
                self.cards_container,
                bg="#ffffff" if cat != self.current_folder_selected else "#dbeafe",
                bd=2,
                relief="raised" if cat != self.current_folder_selected else "solid",
                padx=6,
                pady=4
            )
            card_frame.pack(side=tk.LEFT, padx=4, pady=2)

            card_btn = tk.Button(
                card_frame,
                text=f"📁 {cat}\n({count} items)",
                font=("Segoe UI", 9, "bold"),
                bg="#ffffff" if cat != self.current_folder_selected else "#dbeafe",
                fg="#0f172a" if cat != self.current_folder_selected else "#1d4ed8",
                relief="flat",
                bd=0,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda c=cat: self.select_folder_category(c)
            )
            card_btn.pack(side=tk.TOP, fill=tk.X)

            tree_btn = tk.Button(
                card_frame,
                text="🌳 Tree",
                font=("Segoe UI", 8, "bold"),
                bg="#e0e7ff",
                fg="#4338ca",
                activebackground="#c7d2fe",
                relief="groove",
                bd=1,
                padx=4,
                pady=2,
                cursor="hand2",
                command=lambda c=cat: self.open_tree_visualizer(c)
            )
            tree_btn.pack(side=tk.TOP, fill=tk.X, pady=(4, 0))

    def select_folder_category(self, category_name: str):
        """User clicks on a folder card: opens it and updates properties and file table."""
        self.manager.sync_with_disk(self.organized_dir)
        self.current_folder_selected = category_name
        self.refresh_folder_cards()

        # Update properties card
        if category_name == "All Folders":
            all_docs = self.manager.list_all_documents()
            total_bytes = sum(d.file_size for d in all_docs)
            b_val = float(total_bytes)
            f_size = f"{total_bytes} B"
            for u in ["B", "KB", "MB", "GB"]:
                if b_val < 1024.0 or u == "GB":
                    f_size = f"{b_val:.1f} {u}" if u != "B" else f"{int(b_val)} B"
                    break
                b_val /= 1024.0

            self.lbl_folder_title.config(text="📁 Folder: All Organised Folders (Root View)")
            self.lbl_prop_hash.config(text=f"ROOT_TREE [Capacity {self.manager.storage.capacity}]")
            self.lbl_prop_count.config(text=f"{len(all_docs)} documents")
            self.lbl_prop_size.config(text=f_size)
            self.lbl_prop_types.config(text="Various formats across all folders")
            self.lbl_prop_path.config(text=self.organized_dir)
            self.lbl_table_header.config(text=f"Files Inside: All Organised Folders ({len(all_docs)} files)")
        else:
            props = self.manager.get_category_properties(category_name, self.organized_dir)
            if props:
                self.lbl_folder_title.config(text=f"📂 Folder: {props['category_name']}")
                self.lbl_prop_hash.config(text=props["hash_code"])
                self.lbl_prop_count.config(text=f"{props['file_count']} documents")
                self.lbl_prop_size.config(text=props["formatted_size"])
                self.lbl_prop_types.config(text=props["type_breakdown"])
                self.lbl_prop_path.config(text=props["folder_path"])
                self.lbl_table_header.config(text=f"Files Inside: 📂 {props['category_name']} ({props['file_count']} files)")

        # Run merge sort on the selected folder
        self.handle_merge_sort()
        self.update_diagnostics_display()

    def handle_folder_search(self):
        """Handles folder search bar: finds matching category and displays its properties and Hash-Code."""
        query = self.entry_folder_search.get().strip()
        if not query:
            return

        categories = self.manager.tree.get_categories()
        match = None
        for cat in categories:
            if query.lower() in cat.lower():
                match = cat
                break

        if match:
            self.select_folder_category(match)
            self.lbl_sort_feedback.config(
                text=f"Found folder '{match}'! Properties & Hash-Code loaded."
            )
        else:
            self.lbl_sort_feedback.config(
                text=f"No folder matching '{query}' found."
            )

    def reset_folder_search(self):
        """Clears search and returns to All Folders."""
        self.entry_folder_search.delete(0, tk.END)
        self.select_folder_category("All Folders")

    def handle_merge_sort(self):
        """Executes Custom Merge Sort on the files currently displayed."""
        sort_key_raw = self.combo_sort_key.get()
        key_map = {
            "Filename": "filename",
            "Date of Upload": "upload_timestamp",
            "File Size": "file_size"
        }
        sort_key = key_map.get(sort_key_raw, "filename")
        is_desc = "Descending" in self.combo_sort_order.get()

        target_cat = None if self.current_folder_selected == "All Folders" else self.current_folder_selected

        start_time = time.perf_counter()
        sorted_docs = self.manager.sort_documents(
            category=target_cat,
            sort_by=sort_key,
            reverse=is_desc
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Populate table
        for item in self.doc_table.get_children():
            self.doc_table.delete(item)

        for d in sorted_docs:
            hash_code = self.manager.get_doc_hash_code(d.doc_id)
            self.doc_table.insert(
                "",
                "end",
                values=(
                    d.doc_id,
                    d.filename,
                    d.category,
                    d.formatted_size,
                    d.file_type.upper(),
                    d.formatted_timestamp,
                    hash_code
                )
            )

        order_str = "Desc" if is_desc else "Asc"
        self.lbl_sort_feedback.config(
            text=f"Merge Sort: {len(sorted_docs)} items sorted by '{sort_key_raw}' ({order_str}) in {elapsed_ms:.2f} ms"
        )

    def show_doc_details(self):
        """Opens modal popup when double clicking a document row."""
        selected = self.doc_table.selection()
        if not selected:
            return
        vals = self.doc_table.item(selected[0], "values")
        if not vals:
            return

        doc_id = str(vals[0])
        doc = self.manager.get_document_by_id(doc_id)
        if not doc:
            return

        msg = (
            f"Document ID : {doc.doc_id}\n"
            f"Filename    : {doc.filename}\n"
            f"Category    : {doc.category}\n"
            f"Hash-Code   : {self.manager.get_doc_hash_code(doc.doc_id)}\n"
            f"Size        : {doc.formatted_size} ({doc.file_size} bytes)\n"
            f"File Type   : {doc.file_type.upper()}\n"
            f"Upload Date : {doc.formatted_timestamp}\n"
            f"File Path   : {doc.file_path}\n"
        )
        messagebox.showinfo(f"Document Properties — [{doc.doc_id}]", msg)

    def update_diagnostics_display(self):
        """Updates bottom bar diagnostics from Custom HashMap."""
        stats = self.manager.storage.get_stats()
        self.lbl_p2_diagnostics.config(
            text=(
                f"Custom HashMap: Stored(N)={stats['size']} | "
                f"Capacity(M)={stats['capacity']} | "
                f"LoadFactor={stats['load_factor']:.2f} | "
                f"Collisions={stats['collisions']} | "
                f"MaxChain={stats['max_chain_length']}"
            )
        )

    def open_in_explorer(self, folder_path: str):
        """Cross-platform folder opening in Windows Explorer / OS file manager."""
        folder_path = os.path.abspath(folder_path)
        if os.path.exists(folder_path):
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        else:
            messagebox.showwarning("Folder Missing", f"Folder does not exist yet:\n{folder_path}")

    # =========================================================================
    # FILE SEARCH & RIGHT-CLICK CONTEXT MENU HANDLERS
    # =========================================================================

    def handle_file_live_search(self):
        """
        Filters files in real time across ALL folders via filename/doc_id/file_type.
        Enables cross-folder search so users can find any file regardless of the active folder.
        """
        query = self.entry_file_search.get().strip().lower()
        if not query:
            # Restore current folder view and table header
            self.select_folder_category(self.current_folder_selected)
            return

        # Search across all documents from any folder
        filtered = self.manager.search_by_name(query, category=None)

        for item in self.doc_table.get_children():
            self.doc_table.delete(item)

        for d in filtered:
            h_code = self.manager.get_doc_hash_code(d.doc_id)
            self.doc_table.insert(
                "",
                "end",
                values=(
                    d.doc_id,
                    d.filename,
                    d.category,
                    d.formatted_size,
                    d.file_type.upper(),
                    d.formatted_timestamp,
                    h_code
                )
            )

        categories_found = sorted(list(set(d.category for d in filtered)))
        cat_str = ", ".join(categories_found) if categories_found else "None"
        self.lbl_table_header.config(
            text=f"🔍 Global File Search Results for '{query}' ({len(filtered)} items found across any folder)"
        )
        self.lbl_sort_feedback.config(
            text=f"🔍 Global Search: Found {len(filtered)} file(s) across folders [{cat_str}]"
        )

    def clear_file_search(self):
        """Clears the file search input and restores active folder view."""
        self.entry_file_search.delete(0, tk.END)
        self.select_folder_category(self.current_folder_selected)

    def show_doc_table_context_menu(self, event):
        """Displays right-click popup menu on document rows."""
        row_id = self.doc_table.identify_row(event.y)
        if row_id:
            self.doc_table.selection_set(row_id)
            self.doc_context_menu.post(event.x_root, event.y_root)

    def copy_selected_doc_filename(self):
        """Copies the selected document's filename to the system clipboard."""
        sel = self.doc_table.selection()
        if sel:
            vals = self.doc_table.item(sel[0], "values")
            if vals:
                filename = str(vals[1])
                self.root.clipboard_clear()
                self.root.clipboard_append(filename)
                self.lbl_sort_feedback.config(text=f"📋 Copied to clipboard: '{filename}'")

    def copy_selected_doc_id(self):
        """Copies the selected document's Doc ID to the system clipboard."""
        sel = self.doc_table.selection()
        if sel:
            vals = self.doc_table.item(sel[0], "values")
            if vals:
                doc_id = str(vals[0])
                self.root.clipboard_clear()
                self.root.clipboard_append(doc_id)
                self.lbl_sort_feedback.config(text=f"🆔 Copied Doc ID: '{doc_id}'")

    def copy_selected_doc_hash(self):
        """Copies the selected document's Hash-Code to the system clipboard."""
        sel = self.doc_table.selection()
        if sel:
            vals = self.doc_table.item(sel[0], "values")
            if vals:
                h_code = str(vals[6])
                self.root.clipboard_clear()
                self.root.clipboard_append(h_code)
                self.lbl_sort_feedback.config(text=f"🔑 Copied Hash-Code: '{h_code}'")

    def show_unorg_table_context_menu(self, event):
        """Displays right-click popup menu on unorganized rows."""
        row_id = self.unorganized_table.identify_row(event.y)
        if row_id:
            self.unorganized_table.selection_set(row_id)
            self.unorg_context_menu.post(event.x_root, event.y_root)

    def copy_selected_unorg_filename(self):
        """Copies unorganized file name to system clipboard."""
        sel = self.unorganized_table.selection()
        if sel:
            vals = self.unorganized_table.item(sel[0], "values")
            if vals:
                filename = str(vals[0])
                self.root.clipboard_clear()
                self.root.clipboard_append(filename)
                self.lbl_p1_status.config(text=f"📋 Copied filename: '{filename}'")

    def open_tree_visualizer(self, category_name: str = "All Folders"):
        """
        Opens an interactive modal window displaying the Custom N-ary Tree hierarchy
        (folder_tree.py) for the selected category folder or the entire tree.
        """
        self.manager.sync_with_disk(self.organized_dir)

        win = tk.Toplevel(self.root)
        win.title(f"Custom N-ary Tree Visualizer (folder_tree.py) — {category_name}")
        win.geometry("860x640")
        win.minsize(700, 500)
        win.configure(bg="#f8fafc")

        # Top Banner
        top_bar = tk.Frame(win, bg="#0f172a", padx=16, pady=12)
        top_bar.pack(fill=tk.X)

        title_lbl = tk.Label(
            top_bar,
            text=f"🌳 Custom N-ary Tree Hierarchy: {category_name}",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg="#0f172a"
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = tk.Label(
            top_bar,
            text="Visualizing dsa/folder_tree.py (Root Node -> Category Nodes -> Document Leaf Nodes)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        sub_lbl.pack(anchor=tk.W)

        # Controls Row
        ctrl_frame = tk.Frame(win, bg="#ffffff", bd=1, relief="solid", padx=12, pady=8)
        ctrl_frame.pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Label(ctrl_frame, text="Select Folder to Visualise:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(side=tk.LEFT, padx=(0, 6))

        categories = ["All Folders"] + self.manager.tree.get_categories()
        combo_cat = ttk.Combobox(ctrl_frame, values=categories, state="readonly", width=18)
        combo_cat.set(category_name if category_name in categories else "All Folders")
        combo_cat.pack(side=tk.LEFT, padx=4)

        # Scrolled Text Box for Tree Display
        text_frame = tk.Frame(win, bg="#ffffff", bd=1, relief="solid", padx=8, pady=8)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        scroll_y = ttk.Scrollbar(text_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        txt_tree = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#090d16",
            fg="#38bdf8",
            insertbackground="#ffffff",
            padx=14,
            pady=14,
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        txt_tree.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=txt_tree.yview)
        scroll_x.config(command=txt_tree.xview)

        def refresh_tree_view(cat):
            ascii_text = self.manager.display_tree(category_name=cat)
            txt_tree.config(state=tk.NORMAL)
            txt_tree.delete("1.0", tk.END)
            txt_tree.insert(tk.END, ascii_text)
            txt_tree.config(state=tk.DISABLED)
            title_lbl.config(text=f"🌳 Custom N-ary Tree Hierarchy: {cat}")

        combo_cat.bind("<<ComboboxSelected>>", lambda e: refresh_tree_view(combo_cat.get()))

        # Initial populate
        refresh_tree_view(combo_cat.get())

        # Copy button & Close
        btn_bar = tk.Frame(win, bg="#f8fafc", padx=12, pady=10)
        btn_bar.pack(fill=tk.X)

        def copy_tree_text():
            txt = self.manager.display_tree(category_name=combo_cat.get())
            win.clipboard_clear()
            win.clipboard_append(txt)
            messagebox.showinfo("Tree Copied", "Tree hierarchy copied to clipboard!", parent=win)

        tk.Button(
            btn_bar,
            text="📋 Copy Tree Hierarchy to Clipboard",
            command=copy_tree_text,
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_bar,
            text="Close",
            command=win.destroy,
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.RIGHT)

    def launch_web_ui(self):
        """Launches the modern HTML/CSS/JS web application."""
        import webbrowser
        try:
            subprocess.Popen([sys.executable, "web_app.py"])
            time.sleep(1)
            webbrowser.open("http://127.0.0.1:5000")
        except Exception:
            webbrowser.open("http://127.0.0.1:5000")


def main():
    root = tk.Tk()
    app = DigitalJunkDrawerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
