import customtkinter as ctk
from tkinter import filedialog, messagebox
import sqlite3
import fitz
import os
import shutil
import ctypes
import csv
import io
import re
import json
import time
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from PIL import Image
import urllib.request
from qa_rejections import QARejectionsPane
# ==========================================
# SETTINGS
# ==========================================
APP_VERSION = "3.0.0"

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

import sys
if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.dirname(sys.executable)
    ASSET_DIR = sys._MEIPASS
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSET_DIR = DATA_DIR

DB_NAME = os.path.join(DATA_DIR, "database.db")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
REPOSITORY = os.path.join(DATA_DIR, "repository")
TEMP_FOLDER = os.path.join(DATA_DIR, "temp")

os.makedirs(REPOSITORY, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# COLORS
BG_COLOR = "#f4f7fb"
SIDEBAR_BG = "#0b1a30"
SIDEBAR_HOVER = "#1c2f4d"
SIDEBAR_ACTIVE = "#0066ff"
CARD_BG = "#ffffff"
BORDER_COLOR = "#e0e4e8"
TEXT_PRIMARY = "#1a1a1a"
TEXT_SECONDARY = "#6c757d"
PRIMARY_BLUE = "#0066ff"
STATUS_GREEN_BG = "#e6f4ea"
STATUS_GREEN_FG = "#137333"
STATUS_RED_BG = "#fce8e6"
STATUS_RED_FG = "#c5221f"
STATUS_GRAY_BG = "#f1f3f4"
STATUS_GRAY_FG = "#5f6368"

# QA LOOKUPS
QA_LOOKUPS = {
    "Shift": ["A-SHIFT", "B-SHIFT", "C-SHIFT", "GENERAL"],
    "LOT_NO": ["NA", "LOT-1", "LOT-2", "LOT-3", "LOT-4", "LOT-5"],
    "Line": ["LINE-A", "LINE-B", "LINE-C", "LINE-D", "LINE-E", "AUTOMATION LINE", "SUB ASSEMBLY"],
    "VI-1": ["WEAK WELD", "DUST WELD", "IMPROPER WELD", "AIR BUBBLES", "DAMAGE", "NARROW CHANNEL", "ALIGNMENT ISSUE", "QC TORQUE TEST", "CHILD PARTS WELDED", "HAIR WELD", "DUMP REJECTIONS", "OIL", "BULGING", "NA"],
    "VI-2": ["WEAK WELD", "DUST WELD", "IMPROPER WELD", "AIR BUBBLES", "DAMAGE", "ALIGNMENT ISSUE", "WHITE LINE", "NARROW CHANNEL"],
    "VI-3": ["PEAL OFF", "TEAR OFF", "DAMAGE", "DUST WELD", "IMPROPER WELD", "OVERMELT", "NARROW CHANNEL"],
    "VACCUM REJECTIONS": ["EN 6 LEAK", "EN 4 LEAK", "SN LOW", "SN HIGH", "EN LOW", "EN HIGH", "QR REJECTIONS", "CLOCKED ERROR", "DAMAGE","NA"],
    "VI-4": ["IMPROPER WELDING", "WEAK WELDING", "DUST WELD", "ALIGNMENT ISSUE", "QR REJECTIONS", "DAMAGE", "OVERMELT", "NARROW CHANNEL", "MATRIC REJECTIONS", "SEALING REJECTIONS", "AIR BUBBLES", "WELDING REJECTIONS", "NA"],
    "CHILD PARTS": ["MATRIX", "LEFT VALVE CAPS", "RIGHT VALVE CAPS", "ASSEMBLED SMILEY", "OVERMOULD SMILEY", "GROMMET", "NA", "SMILEY", "FILTER RODS", "SAMPLE FILTER", "SMALL DUMP", "QR CODE LABELS", "VALVE BODY"],
    "Equipment_LINE-A": ["EC/EQID/III-00631", "EC/EQID/III-00163"],
    "Equipment_LINE-B": ["EC/EQID/III-00572", "EC/EQID/III-00133"],
    "Equipment_LINE-C": ["EC/EQID/III-00069", "EC/EQID/III-00101"],
    "Equipment_LINE-D": ["EC/EQID/III-00003", "EC/EQID/III-00633"],
    "Equipment_LINE-E": ["EC/EQID/III-00036", "EC/EQID/III-00632"],
    "Equipment_AUTOMATION LINE": ["EC/EQID/III-00659"],
    "Equipment_SUB ASSEMBLY": ["NA"],
    "CartridgePart": ["NA", "BUFFER CHANNEL SIDE","ELUTE SIDE", "MATRIX SIDE", "SAMPLE FILETER SIDE", "DUMP SIDE", "FILTER RODS SIDE", "SAMPLE FILTER BOTTOM","VALVE CAP DAMAGE", "IN CHANNEL", "QR CODE"],
    "VerifiedByName": ["L R NAIDU", "KAUSHIK", "SAI KUMAR", "SRINU", "ROHINII", "KISHORE", "RAJU", "RAVI TEJA","AZAD"]
}
STAGE_OPTIONS = ["VI-1", "VI-2", "VI-3", "VACCUM REJECTIONS", "VI-4", "CHILD PARTS"]

class ControlledPrintSystem(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Controlled Document Printing System - v{APP_VERSION}")
        self.geometry("1300x750")
        self.configure(fg_color=BG_COLOR)
        
        self.silent_print_var = ctk.BooleanVar(value=False)
        self.selected_printer_var = ctk.StringVar(value="")
        
        icon_path = os.path.join(ASSET_DIR, "app_icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.check_license_sync()

    def get_machine_id(self):
        import uuid
        import platform
        mac = str(uuid.getnode())
        pc = platform.node()
        return f"{pc}-{mac}"
        
    def check_license_sync(self):
        import getpass
        
        self.machine_id = self.get_machine_id()
        self.username = getpass.getuser()
        
        url = "https://script.google.com/macros/s/AKfycbzJAtz2MktkFtBL1EKO2kWWXANvSNCTEkvSLHPVieR_qDTylxrtN1zT6tlorSrTVwF48w/exec"
        payload = {
            "action": "checkLicense",
            "machineId": self.machine_id,
            "username": self.username
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                if res_data.get("status") == "active":
                    self.build_login_screen()
                else:
                    self.build_blocked_screen()
        except Exception as e:
            print("License check failed:", e)
            self.build_blocked_screen(offline=True)

    def build_blocked_screen(self, offline=False):
        self.blocked_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.blocked_frame.pack(fill="both", expand=True)
        
        card = ctk.CTkFrame(self.blocked_frame, width=650, height=450, corner_radius=15, fg_color=CARD_BG, border_width=1, border_color=STATUS_RED_FG)
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        title = "Official Permission Required" if not offline else "Connection Error"
        
        msg = (
            "Dear QA Team,\n\n"
            "This software was developed by Kaushik, and all rights are reserved by me.\n"
            "If you wish to use this software, please obtain official permission from the QA Head.\n"
            "Once the approval is received, I will make the software available for official use.\n\n"
            "Note: The free service/support period has been completed.\n\n"
            "Regards,\n"
            "Kaushik\n\n"
            f"(Machine ID: {getattr(self, 'machine_id', 'UNKNOWN')})"
        )
        
        if offline:
            msg = "Could not connect to the licensing server.\nPlease check your internet connection and try again."
            
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=20, weight="bold"), text_color=STATUS_RED_FG)
        lbl_title.pack(pady=(40, 10))
        
        lbl_msg = ctk.CTkLabel(card, text=msg, font=ctk.CTkFont(size=14), text_color=TEXT_PRIMARY, justify="center")
        lbl_msg.pack(padx=30, pady=20)
        
        btn = ctk.CTkButton(card, text="Retry Connection", command=lambda: [self.blocked_frame.destroy(), self.check_license_sync()])
        btn.pack(pady=20)

    def build_login_screen(self):
        self.login_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.login_frame.pack(fill="both", expand=True)
        
        # DNA Theme Background
        bg_path = os.path.join(ASSET_DIR, "dna_bg.png")
        if os.path.exists(bg_path):
            try:
                bg_img = Image.open(bg_path)
                bg_ctk_img = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(1300, 750))
                bg_lbl = ctk.CTkLabel(self.login_frame, text="", image=bg_ctk_img)
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print("Could not load DNA background:", e)
        
        # Center card
        card = ctk.CTkFrame(self.login_frame, width=400, height=500, corner_radius=15, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR)
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title
        logo_path = os.path.join(ASSET_DIR, "molbio_logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # calculate width to maintain aspect ratio for a height of 60
                w, h = img.size
                new_w = int((60 / h) * w)
                logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, 60))
                logo_lbl = ctk.CTkLabel(card, text="", image=logo_img)
                logo_lbl.pack(pady=(30, 10))
            except Exception as e:
                print("Could not load logo:", e)
        
        subtitle = ctk.CTkLabel(card, text="Please login to continue", font=ctk.CTkFont(size=14), text_color=TEXT_SECONDARY)
        subtitle.pack(pady=(0, 30))
        
        # Inputs
        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        
        user_lbl = ctk.CTkLabel(card, text="Username", text_color=TEXT_PRIMARY, font=ctk.CTkFont(weight="bold"))
        user_lbl.pack(anchor="w", padx=40)
        user_entry = ctk.CTkEntry(card, textvariable=self.username_var, height=40, placeholder_text="Enter ID")
        user_entry.pack(fill="x", padx=40, pady=(5, 15))
        
        pass_lbl = ctk.CTkLabel(card, text="Password", text_color=TEXT_PRIMARY, font=ctk.CTkFont(weight="bold"))
        pass_lbl.pack(anchor="w", padx=40)
        
        pass_frame = ctk.CTkFrame(card, fg_color="transparent")
        pass_frame.pack(fill="x", padx=40, pady=(5, 10))
        
        self.pass_entry = ctk.CTkEntry(pass_frame, textvariable=self.password_var, show="•", height=40, placeholder_text="Enter Password")
        self.pass_entry.pack(side="left", fill="x", expand=True)
        
        self.show_pass = False
        def toggle_password():
            self.show_pass = not self.show_pass
            self.pass_entry.configure(show="" if self.show_pass else "•")
            eye_btn.configure(text="Hide" if self.show_pass else "Show")

        eye_btn = ctk.CTkButton(pass_frame, text="Show", width=50, height=40, fg_color="transparent", hover_color=STATUS_GRAY_BG, text_color=TEXT_SECONDARY, font=ctk.CTkFont(weight="bold"), command=toggle_password)
        eye_btn.pack(side="right", padx=(5, 0))
        
        self.login_error_lbl = ctk.CTkLabel(card, text="", text_color=STATUS_RED_FG)
        self.login_error_lbl.pack(pady=5)
        
        login_btn = ctk.CTkButton(card, text="Login", height=45, font=ctk.CTkFont(size=16, weight="bold"), command=self.attempt_login)
        login_btn.pack(fill="x", padx=40, pady=(10, 40))
        
        # Bind enter key
        self.bind('<Return>', lambda e: self.attempt_login())

    def attempt_login(self):
        user = self.username_var.get().strip()
        pwd = self.password_var.get()
        if user == "admin" and pwd == "Molbio@qa":
            self.unbind('<Return>')
            self.login_frame.destroy()
            self.init_main_app()
            self.log_audit("admin", "LOGIN", "User admin logged in successfully")
        else:
            self.login_error_lbl.configure(text="Incorrect ID or password")

    def auto_clean_temp_files(self):
        import time
        if not os.path.exists(TEMP_FOLDER): return
        now = time.time()
        for f in os.listdir(TEMP_FOLDER):
            try:
                fp = os.path.join(TEMP_FOLDER, f)
                if os.path.isfile(fp):
                    # If file is older than 24 hours
                    if os.stat(fp).st_mtime < now - 86400:
                        os.remove(fp)
            except Exception as e:
                print(f"Failed to auto-clean {f}: {e}")

    def init_main_app(self):
        # Settings Variables
        self.watermark_text = ctk.StringVar(value="AUTHORISED COPY")
        self.watermark_fontsize = ctk.IntVar(value=18)
        self.watermark_fontname = ctk.StringVar(value="Arial")
        self.watermark_opacity = ctk.DoubleVar(value=0.60)
        self.watermark_x_offset = ctk.IntVar(value=0)
        self.watermark_y_offset = ctk.IntVar(value=0)
        self.watermark_pixel_jump = ctk.IntVar(value=5)
        self.github_repo = ctk.StringVar(value="kaushik565/controlled-print-system")
        self.favorites = [None] * 6
        self.current_preview_log = None
        self.error_logs = []
        
        self.auto_clean_temp_files()
        
        self.watermark_text.trace_add("write", self.refresh_preview)
        self.silent_print_var.trace_add("write", lambda *args: self.save_settings())
        self.selected_printer_var.trace_add("write", lambda *args: self.save_settings())
        self.watermark_pixel_jump.trace_add("write", lambda *args: self.save_settings())
        self.github_repo.trace_add("write", lambda *args: self.save_settings())
        
        self.load_settings()
        
        self.check_for_updates()
        
        self.create_database()
        self.cleanup_old_logs()
        
        try:
            self.icon_print = ctk.CTkImage(Image.open(os.path.join(ASSET_DIR, "assets", "print.png")), size=(20, 20))
            self.icon_eye = ctk.CTkImage(Image.open(os.path.join(ASSET_DIR, "assets", "eye.png")), size=(20, 20))
            self.icon_refresh = ctk.CTkImage(Image.open(os.path.join(ASSET_DIR, "assets", "refresh.png")), size=(20, 20))
            self.icon_delete = ctk.CTkImage(Image.open(os.path.join(ASSET_DIR, "assets", "delete.png")), size=(20, 20))
        except Exception as e:
            print("Could not load icons:", e)
            self.icon_print = None
            self.icon_eye = None
            self.icon_refresh = None
            self.icon_delete = None
        
        # State
        self.parsed_logs = []  # List of dicts representing table rows
        
        self.build_ui()

    def logout(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.build_login_screen()

    def create_database(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            format_id TEXT,
            revision TEXT,
            file_path TEXT,
            status TEXT
        )
        """)
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN inactive_date TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS print_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT,
            format_id TEXT,
            revision TEXT,
            copies_info TEXT,
            print_date TEXT,
            status TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            action TEXT,
            details TEXT
        )
        """)

        conn.commit()
        conn.close()

    def check_for_updates(self):
        repo = self.github_repo.get().strip()
        if not repo:
            return
            
        def _check():
            import urllib.request
            import json
            try:
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    
                latest_tag = data.get('tag_name', '').replace('v', '')
                if not latest_tag: return
                
                # Compare versions
                current_v = [int(x) for x in APP_VERSION.split('.')]
                latest_v = [int(x) for x in latest_tag.split('.')]
                
                if latest_v > current_v:
                    # Find the exe asset
                    download_url = None
                    for asset in data.get('assets', []):
                        if asset['name'].endswith('.exe'):
                            download_url = asset['browser_download_url']
                            break
                            
                    if download_url:
                        self.after(0, lambda: self.prompt_update(latest_tag, download_url))
            except Exception as e:
                print(f"Update check failed: {e}")
                
        import threading
        threading.Thread(target=_check, daemon=True).start()
        
    def prompt_update(self, version, download_url):
        from tkinter import messagebox
        if messagebox.askyesno("Update Available", f"Version {version} is available!\n\nWould you like to download and install it now?"):
            self.perform_update(download_url)
            
    def perform_update(self, download_url):
        import urllib.request
        import threading
        
        # Show a downloading popup
        popup = ctk.CTkToplevel(self)
        popup.title("Updating...")
        popup.geometry("300x150")
        popup.attributes("-topmost", True)
        lbl = ctk.CTkLabel(popup, text="Downloading update, please wait...", font=ctk.CTkFont(weight="bold"))
        lbl.pack(pady=40)
        
        def _download():
            try:
                import sys, os
                exe_path = sys.executable
                if not getattr(sys, 'frozen', False):
                    # Not running as an exe
                    self.after(0, popup.destroy)
                    return
                    
                new_exe = exe_path + ".new"
                urllib.request.urlretrieve(download_url, new_exe)
                
                # Write bat script
                bat_path = os.path.join(os.path.dirname(exe_path), "update.bat")
                with open(bat_path, "w") as f:
                    f.write("@echo off\n")
                    f.write("timeout /t 2 /nobreak > NUL\n")
                    f.write(f'move /Y "{new_exe}" "{exe_path}"\n')
                    f.write(f'start "" "{exe_path}"\n')
                    f.write('del "%~f0"\n')
                    
                import subprocess
                subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
                os._exit(0)
            except Exception as e:
                self.after(0, popup.destroy)
                print(f"Update failed: {e}")
                
        threading.Thread(target=_download, daemon=True).start()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                if 'watermark_text' in data: self.watermark_text.set(data['watermark_text'])
                if 'watermark_fontsize' in data: self.watermark_fontsize.set(data['watermark_fontsize'])
                if 'watermark_fontname' in data: self.watermark_fontname.set(data['watermark_fontname'])
                if 'watermark_opacity' in data: self.watermark_opacity.set(data['watermark_opacity'])
                if 'watermark_x_offset' in data: self.watermark_x_offset.set(data['watermark_x_offset'])
                if 'watermark_y_offset' in data: self.watermark_y_offset.set(data['watermark_y_offset'])
                if 'watermark_pixel_jump' in data: self.watermark_pixel_jump.set(data['watermark_pixel_jump'])
                if 'silent_print_var' in data: self.silent_print_var.set(data['silent_print_var'])
                if 'selected_printer_var' in data: self.selected_printer_var.set(data['selected_printer_var'])
                
                if 'github_repo' in data and data['github_repo'].strip(): 
                    self.github_repo.set(data['github_repo'])
                else:
                    self.github_repo.set("kaushik565/controlled-print-system")
                
                if 'favorites' in data and isinstance(data['favorites'], list):
                    loaded_favs = data['favorites']
                    self.favorites = loaded_favs + [None] * (6 - len(loaded_favs))
                    self.favorites = self.favorites[:6]
                    
            except Exception as e:
                print("Error loading settings:", e)

    def save_settings(self):
        data = {
            'watermark_text': self.watermark_text.get(),
            'watermark_fontsize': self.watermark_fontsize.get(),
            'watermark_fontname': self.watermark_fontname.get(),
            'watermark_opacity': self.watermark_opacity.get(),
            'watermark_x_offset': self.watermark_x_offset.get(),
            'watermark_y_offset': self.watermark_y_offset.get(),
            'watermark_pixel_jump': self.watermark_pixel_jump.get(),
            'silent_print_var': self.silent_print_var.get(),
            'selected_printer_var': self.selected_printer_var.get(),
            'github_repo': self.github_repo.get(),
            'favorites': getattr(self, 'favorites', [None]*6)
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print("Error saving settings:", e)

    def build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main
        
        self.pages_container = ctk.CTkFrame(self, fg_color="transparent")
        self.pages_container.grid(row=0, column=1, sticky="nsew")
        self.pages_container.grid_rowconfigure(0, weight=1)
        self.pages_container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        # Build Batch Print Frame
        self.frames["🖨️ Batch Print"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["🖨️ Batch Print"].grid_rowconfigure(0, weight=1)
        self.frames["🖨️ Batch Print"].grid_columnconfigure(0, weight=3, uniform="col")
        self.frames["🖨️ Batch Print"].grid_columnconfigure(1, weight=2, uniform="col")
        
        self.build_main_pane(self.frames["🖨️ Batch Print"])
        self.build_preview_pane(self.frames["🖨️ Batch Print"])
        
        # Build QA Rejections Frame
        self.frames["📊 QA Rejections"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["📊 QA Rejections"].grid_rowconfigure(0, weight=1)
        self.frames["📊 QA Rejections"].grid_columnconfigure(0, weight=1)
        self.build_qa_rejections_pane(self.frames["📊 QA Rejections"])
        
        # Build Document Repository Frame
        self.frames["📄 Document Repository"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["📄 Document Repository"].grid_rowconfigure(0, weight=1)
        self.frames["📄 Document Repository"].grid_columnconfigure(0, weight=1)
        self.build_repository_pane(self.frames["📄 Document Repository"])
        
        # Build Print History Frame
        self.frames["🕒 Print History"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["🕒 Print History"].grid_rowconfigure(0, weight=1)
        self.frames["🕒 Print History"].grid_columnconfigure(0, weight=1)
        self.build_print_history_pane(self.frames["🕒 Print History"])

        # Build Audit Log Frame
        self.frames["📋 Audit Log"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["📋 Audit Log"].grid_rowconfigure(0, weight=1)
        self.frames["📋 Audit Log"].grid_columnconfigure(0, weight=1)
        self.build_audit_log_pane(self.frames["📋 Audit Log"])
        
        # Build Error Log Frame
        self.frames["⚠️ Error Log"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["⚠️ Error Log"].grid_rowconfigure(0, weight=1)
        self.frames["⚠️ Error Log"].grid_columnconfigure(0, weight=1)
        self.build_error_log_pane(self.frames["⚠️ Error Log"])
        
        # Build Settings Frame
        self.frames["⚙️ Settings"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["⚙️ Settings"].grid_rowconfigure(0, weight=1)
        self.frames["⚙️ Settings"].grid_columnconfigure(0, weight=1)
        self.build_settings_pane(self.frames["⚙️ Settings"])

        # Build About Frame
        self.frames["ℹ️ About"] = ctk.CTkFrame(self.pages_container, fg_color="transparent")
        self.frames["ℹ️ About"].grid_rowconfigure(0, weight=1)
        self.frames["ℹ️ About"].grid_columnconfigure(0, weight=1)
        self.build_about_pane(self.frames["ℹ️ About"])
        
            
        self.sidebar_buttons = {}
        self.build_sidebar()
        self.build_status_bar()
        self.switch_frame("🖨️ Batch Print")
        self.toggle_right_pane()

    def switch_frame(self, name):
        for f in self.frames.values():
            f.grid_forget()
        if name in self.frames:
            self.frames[name].grid(row=0, column=0, sticky="nsew")
            if name == "📄 Document Repository":
                self.load_repository_data()
            elif name == "🕒 Print History":
                self.load_print_history_data()
            elif name == "📋 Audit Log":
                self.load_audit_log_data()
            elif name == "⚠️ Error Log":
                self.load_error_log_data()
        
        for btn_name, btn in self.sidebar_buttons.items():
            if btn_name == name:
                btn.configure(fg_color=SIDEBAR_ACTIVE, hover_color=SIDEBAR_ACTIVE)
            else:
                btn.configure(fg_color="transparent", hover_color=SIDEBAR_HOVER)

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        # Logo/Title
        logo_path = os.path.join(ASSET_DIR, "molbio_logo_white.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # scale width to 160 pixels to fit the sidebar nicely, calculate height proportionally
                w, h = img.size
                new_w = 160
                new_h = int((new_w / w) * h)
                
                sidebar_logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                title_label = ctk.CTkLabel(self.sidebar, text="", image=sidebar_logo_img)
            except Exception as e:
                print("Could not load logo for sidebar:", e)
                title_label = ctk.CTkLabel(self.sidebar, text="MOLBIO", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        else:
            title_label = ctk.CTkLabel(self.sidebar, text="MOLBIO", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
            
        title_label.pack(pady=(30, 40), padx=20, anchor="center")

        # Menu Items
        menu_items = [
            ("📄 Document Repository", False),
            ("🖨️ Batch Print", True), # Active
            ("🕒 Print History", False),
            ("📊 QA Rejections", False),
            ("📋 Audit Log", False),
            ("⚠️ Error Log", False),
            ("⚙️ Settings", False),
            ("ℹ️ About", False)
        ]

        for text, is_active in menu_items:
            btn = ctk.CTkButton(
                self.sidebar, text=text, fg_color="transparent", hover_color=SIDEBAR_HOVER,
                anchor="w", font=ctk.CTkFont(size=14), height=40, corner_radius=8,
                command=lambda t=text: self.switch_frame(t)
            )
            btn.pack(pady=5, padx=15, fill="x")
            self.sidebar_buttons[text] = btn

        # User Profile
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(side="bottom", fill="x", pady=20, padx=15)
        user_label = ctk.CTkLabel(user_frame, text="👤 QA_ADMIN\nQA Department", text_color="white", justify="left")
        user_label.pack(side="left")
        
        logout_btn = ctk.CTkButton(user_frame, text="Logout", width=60, fg_color=STATUS_RED_FG, hover_color="#8b0000", command=self.logout)
        logout_btn.pack(side="right")

    def build_main_pane(self, parent):
        self.main_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1) # Table takes remaining space

        # Header
        header = ctk.CTkLabel(self.main_frame, text="Batch Document Printing", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.grid(row=0, column=0, sticky="w", pady=(0, 20))


        # Input Area
        input_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_container.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        input_container.grid_columnconfigure(0, weight=3)
        input_container.grid_columnconfigure(1, weight=1)

        # Left Textbox
        left_input = ctk.CTkFrame(input_container, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        left_input.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.log_text = ctk.CTkTextbox(left_input, height=120, font=ctk.CTkFont(family="Consolas", size=13), fg_color="transparent", text_color=TEXT_PRIMARY)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.insert("1.0", "Paste Excel batch log here...")
        
        def clear_placeholder(event):
            if self.log_text.get("1.0", "end-1c").strip() == "Paste Excel batch log here...":
                self.log_text.delete("1.0", "end")
        
        def add_placeholder(event):
            if not self.log_text.get("1.0", "end-1c").strip():
                self.log_text.insert("1.0", "Paste Excel batch log here...")
                
        self.log_text.bind("<FocusIn>", clear_placeholder)
        self.log_text.bind("<Button-1>", clear_placeholder)
        self.log_text.bind("<FocusOut>", add_placeholder)

        # Right Actions
        right_actions = ctk.CTkFrame(input_container, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        right_actions.grid(row=0, column=1, sticky="nsew")
        
        action_title = ctk.CTkLabel(right_actions, text="Quick Actions", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        action_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        load_btn = ctk.CTkButton(right_actions, text="📄 Upload Master PDF", fg_color="transparent", border_width=1, text_color=TEXT_PRIMARY, command=self.upload_document)
        load_btn.pack(pady=5, padx=15, fill="x")
        
        clear_btn = ctk.CTkButton(right_actions, text="🗑️ Clear Data", fg_color="transparent", border_width=1, text_color=STATUS_RED_FG, border_color=STATUS_RED_FG, command=self.clear_queue)
        clear_btn.pack(pady=5, padx=15, fill="x")
        
        process_btn = ctk.CTkButton(right_actions, text="▶ Process Data", fg_color=PRIMARY_BLUE, command=self.process_log)
        process_btn.pack(pady=5, padx=15, fill="x")

        # Data Table Container
        table_container = ctk.CTkFrame(self.main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        table_container.grid(row=3, column=0, sticky="nsew", pady=(0, 20))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        table_header = ctk.CTkFrame(table_container, fg_color="transparent", height=40)
        table_header.grid(row=0, column=0, sticky="ew")
        table_title = ctk.CTkLabel(table_header, text="Batch Log Data", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        table_title.pack(side="left", padx=15, pady=10)
        
        self.table_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        for i in range(7):
            self.table_scroll.grid_columnconfigure(i, weight=1)

        # Summary Area
        summary_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        summary_container.grid(row=4, column=0, sticky="ew")
        summary_container.grid_columnconfigure(0, weight=1)
        summary_container.grid_columnconfigure(1, weight=1)

        stats_frame = ctk.CTkFrame(summary_container, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.stat_total = ctk.CTkLabel(stats_frame, text="Total: 0", font=ctk.CTkFont(size=16, weight="bold"), text_color=PRIMARY_BLUE)
        self.stat_total.pack(side="left", padx=20, pady=15)
        self.stat_pending = ctk.CTkLabel(stats_frame, text="Pending: 0", text_color=TEXT_SECONDARY)
        self.stat_pending.pack(side="left", padx=20)
        self.stat_printed = ctk.CTkLabel(stats_frame, text="Printed: 0", text_color=STATUS_GREEN_FG)
        self.stat_printed.pack(side="left", padx=20)
        self.stat_error = ctk.CTkLabel(stats_frame, text="Error: 0", text_color=STATUS_RED_FG)
        self.stat_error.pack(side="left", padx=20)

        bulk_frame = ctk.CTkFrame(summary_container, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        bulk_frame.grid(row=0, column=1, sticky="nsew")
        
        self.print_all_btn = ctk.CTkButton(bulk_frame, text="🖨️ Print Pending", fg_color=STATUS_GREEN_FG, hover_color="#0d5224", command=self.print_all_pending)
        self.print_all_btn.pack(side="right", padx=15, pady=15)

        self.render_table() # Renders empty headers

    def build_preview_pane(self, parent):
        self.preview_pane = ctk.CTkFrame(parent, fg_color="#eaeff5", corner_radius=0)
        self.preview_pane.grid(row=0, column=1, sticky="nsew")
        self.preview_pane.grid_rowconfigure(1, weight=1)
        self.preview_pane.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.preview_pane, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        preview_title = ctk.CTkLabel(header_frame, text="Document Preview", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY)
        preview_title.pack(side="left")
        
        rotate_btn = ctk.CTkButton(header_frame, text="↻ Rotate", width=80, fg_color=PRIMARY_BLUE, command=self.rotate_preview)
        rotate_btn.pack(side="right")

        # Preview Image Area
        self.preview_canvas = ctk.CTkFrame(self.preview_pane, fg_color=CARD_BG, corner_radius=5, border_width=1, border_color=BORDER_COLOR)
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.preview_canvas.grid_rowconfigure(0, weight=1)
        self.preview_canvas.grid_columnconfigure(0, weight=1)

        self.preview_image_label = ctk.CTkLabel(self.preview_canvas, text="Select a document (👁️) to preview", text_color=TEXT_SECONDARY)
        self.preview_image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Print Settings Area
        self.settings_frame = ctk.CTkFrame(self.preview_pane, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        set_title = ctk.CTkLabel(self.settings_frame, text="Watermark Settings", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        set_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        grid_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Favorites Area (Hidden when preview is active)
        self.favorites_frame = ctk.CTkFrame(self.preview_pane, fg_color="transparent")
        self.favorites_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        row1_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        row1_frame.pack(fill="x", pady=(0, 10))
        
        size_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        size_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        size_lbl = ctk.CTkLabel(size_frame, text="Watermark Size:", text_color=TEXT_SECONDARY)
        size_lbl.pack(anchor="w", pady=(0, 0))
        self.wm_size_dropdown = ctk.CTkOptionMenu(size_frame, values=[str(i) for i in range(9, 21)], variable=ctk.StringVar(value=str(self.watermark_fontsize.get())), command=lambda v: [self.watermark_fontsize.set(int(v)), self.refresh_preview()])
        self.wm_size_dropdown.pack(fill="x")
        
        font_frame = ctk.CTkFrame(row1_frame, fg_color="transparent")
        font_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        font_lbl = ctk.CTkLabel(font_frame, text="Watermark Font:", text_color=TEXT_SECONDARY)
        font_lbl.pack(anchor="w", pady=(0, 0))
        self.wm_font_dropdown = ctk.CTkOptionMenu(font_frame, values=["Arial", "Helvetica", "Times New Roman", "Courier"], variable=self.watermark_fontname, command=lambda _: self.refresh_preview())
        self.wm_font_dropdown.pack(fill="x")
        
        op_lbl = ctk.CTkLabel(left_col, text="Watermark Opacity:", text_color=TEXT_SECONDARY)
        op_lbl.pack(anchor="w", pady=(0, 0))
        self.opacity_slider = ctk.CTkSlider(left_col, from_=0.1, to=1.0, number_of_steps=90, variable=self.watermark_opacity, command=self.refresh_preview)
        self.opacity_slider.pack(fill="x", pady=(0, 0))

        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="e", padx=(10, 0))

        pad_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        pad_frame.pack(pady=(15, 0))
        
        up_btn = ctk.CTkButton(pad_frame, text="▲", width=30, height=30, command=lambda: self.move_watermark(0, -1))
        up_btn.grid(row=0, column=1, pady=2)
        left_btn = ctk.CTkButton(pad_frame, text="◀", width=30, height=30, command=lambda: self.move_watermark(-1, 0))
        left_btn.grid(row=1, column=0, padx=2)
        right_btn = ctk.CTkButton(pad_frame, text="▶", width=30, height=30, command=lambda: self.move_watermark(1, 0))
        right_btn.grid(row=1, column=2, padx=2)
        down_btn = ctk.CTkButton(pad_frame, text="▼", width=30, height=30, command=lambda: self.move_watermark(0, 1))
        down_btn.grid(row=2, column=1, pady=2)
    def move_watermark(self, dx_sign, dy_sign):
        jump = self.watermark_pixel_jump.get()
        self.watermark_x_offset.set(self.watermark_x_offset.get() + (dx_sign * jump))
        self.watermark_y_offset.set(self.watermark_y_offset.get() + (dy_sign * jump))
        self.refresh_preview()

    def refresh_preview(self, *args):
        self.save_settings()
        if self.current_preview_log:
            # We add a small delay to avoid lagging while typing
            if hasattr(self, '_preview_after_id') and self._preview_after_id:
                self.after_cancel(self._preview_after_id)
            self._preview_after_id = self.after(200, lambda: self.preview_document(self.current_preview_log, force_refresh=True))


    def toggle_right_pane(self):
        if getattr(self, 'current_preview_log', None) is not None:
            self.favorites_frame.grid_remove()
            self.settings_frame.grid()
        else:
            self.settings_frame.grid_remove()
            self.favorites_frame.grid()
            self.render_favorites()

    def render_favorites(self):
        for widget in self.favorites_frame.winfo_children():
            widget.destroy()
            
        title_lbl = ctk.CTkLabel(self.favorites_frame, text="Favorite Documents", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY)
        title_lbl.pack(anchor="w", padx=5, pady=(0, 10))
        
        cards_container = ctk.CTkFrame(self.favorites_frame, fg_color="transparent")
        cards_container.pack(fill="both", expand=True)
        
        cards_container.grid_columnconfigure((0, 1), weight=1, uniform="col")
        cards_container.grid_rowconfigure((0, 1, 2), weight=1, uniform="row")
        
        for i in range(6):
            row = i // 2
            col = i % 2
            fav_data = getattr(self, 'favorites', [None]*6)[i]
            
            card = ctk.CTkFrame(cards_container, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_rowconfigure(0, weight=1)
            card.grid_columnconfigure(0, weight=1)
            
            if not fav_data:
                add_btn = ctk.CTkButton(card, text="+", font=ctk.CTkFont(size=40, weight="bold"), text_color=TEXT_SECONDARY, fg_color="transparent", hover_color=BG_COLOR, command=lambda idx=i: self.add_favorite(idx))
                add_btn.grid(row=0, column=0, sticky="nsew")
            else:
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                
                title_lbl = ctk.CTkLabel(inner, text=fav_data.get('custom_name', 'Favorite'), font=ctk.CTkFont(size=14, weight="bold"), text_color=PRIMARY_BLUE)
                title_lbl.pack(anchor="w")
                
                import os
                filename = os.path.basename(fav_data.get('file_path', ''))
                doc_lbl = ctk.CTkLabel(inner, text=filename, font=ctk.CTkFont(size=10), text_color=TEXT_SECONDARY)
                doc_lbl.pack(anchor="w", pady=(0, 10))
                
                btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
                btn_frame.pack(fill="x", side="bottom", expand=True, anchor="s")
                
                print_btn = ctk.CTkButton(btn_frame, text="🖨️ Print", height=24, fg_color=STATUS_GREEN_FG, hover_color="#228B22", command=lambda idx=i: self.print_favorite(idx))
                print_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
                
                del_btn = ctk.CTkButton(btn_frame, text="🗑", width=28, height=24, fg_color=STATUS_RED_FG, hover_color="#8b0000", command=lambda idx=i: self.remove_favorite(idx))
                del_btn.pack(side="right")

    def add_favorite(self, index):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")], title="Select Document for Favorite")
        if not file_path: return
            
        import os
        import shutil
        filename = os.path.basename(file_path)
        parts = filename.replace('.pdf', '').split('_')
        format_id = parts[0] if len(parts) > 0 else filename
        revision = parts[1] if len(parts) > 1 else "00"
        
        dialog = ctk.CTkInputDialog(text=f"Enter a name for this favorite:", title="Add Favorite")
        custom_name = dialog.get_input()
        if not custom_name: return
            
        dest_path = os.path.join(REPOSITORY, filename)
        if not os.path.exists(dest_path):
            try:
                shutil.copy2(file_path, dest_path)
            except Exception as e:
                self.show_modern_error(f"Failed to copy file: {e}")
                return
                
        self.favorites[index] = {
            "custom_name": custom_name,
            "format_id": format_id,
            "revision": revision,
            "file_path": dest_path
        }
        self.save_settings()
        self.render_favorites()

    def remove_favorite(self, index):
        self.favorites[index] = None
        self.save_settings()
        self.render_favorites()

    def print_favorite(self, index):
        fav_data = getattr(self, 'favorites', [None]*6)[index]
        if not fav_data: return
        
        import os
        from datetime import datetime
        
        pdf_path = fav_data.get('file_path')
        if not pdf_path or not os.path.exists(pdf_path):
            self.show_modern_error("Favorite document file could not be found on disk.")
            return

        timestamp = datetime.now().strftime("%H%M%S")
        output_pdf = os.path.join(TEMP_FOLDER, f"FAV_{timestamp}.pdf")
        parsed_copies = [{"page": None, "copies": 1}]
        
        try:
            # Empty batch_no ensures the system defaults to "AUTHORISED COPY <date>"
            new_doc = self.generate_watermarked_doc(pdf_path, parsed_copies, "", 0)
            new_doc.save(output_pdf)
            new_doc.close()
            
            if self.silent_print_var.get() and self.selected_printer_var.get() != "No printers found":
                import win32api
                win32api.ShellExecute(0, "printto", output_pdf, f'"{self.selected_printer_var.get()}"', ".", 0)
            else:
                os.startfile(output_pdf)
                
            self.show_status_msg(f"Opened Favorite: {fav_data['custom_name']}")
        except Exception as e:
            self.show_modern_error(f"Failed to generate Favorite: {e}")

    def build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=CARD_BG, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_lbl = ctk.CTkLabel(self.status_bar, text="", text_color=STATUS_GREEN_FG, font=ctk.CTkFont(size=12))
        self.status_lbl.pack(side="left", padx=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_bar, width=300, height=10, progress_color=PRIMARY_BLUE)
        self.progress_bar.set(0)
        
        self.time_lbl = ctk.CTkLabel(self.status_bar, text="", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        self.time_lbl.pack(side="right", padx=(10, 20))
        
        self.db_lbl = ctk.CTkLabel(self.status_bar, text="🟢 DB: Connected", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        self.db_lbl.pack(side="right", padx=10)
        
        self.cache_lbl = ctk.CTkLabel(self.status_bar, text="🧹 Temp Cache: 0 KB", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        self.cache_lbl.pack(side="right", padx=10)
        
        self.credit_lbl = ctk.CTkLabel(self.status_bar, text="Designed & Developed By QA Team - SITE III", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=11, weight="bold"))
        self.credit_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.update_status_bar_metrics()

    def show_status_msg(self, text, is_error=False, duration=3000):
        color = STATUS_RED_FG if is_error else STATUS_GREEN_FG
        icon = "🔴" if is_error else "🟢"
        self.status_lbl.configure(text=f"{icon} {text}", text_color=color)
        
        if hasattr(self, '_status_timer') and self._status_timer:
            self.after_cancel(self._status_timer)
            
        if duration > 0:
            self._status_timer = self.after(duration, lambda: self.status_lbl.configure(text="", text_color=STATUS_GREEN_FG))

    def show_modern_error(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x220")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 110
        popup.geometry(f"+{x}+{y}")
        
        popup.configure(fg_color=CARD_BG)
        
        icon_lbl = ctk.CTkLabel(popup, text="⚠️", font=ctk.CTkFont(size=40))
        icon_lbl.pack(pady=(20, 5))
        
        title_lbl = ctk.CTkLabel(popup, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=STATUS_RED_FG)
        title_lbl.pack(pady=0)
        
        msg_lbl = ctk.CTkLabel(popup, text=message, font=ctk.CTkFont(size=13), text_color=TEXT_PRIMARY, wraplength=350, justify="center")
        msg_lbl.pack(pady=(10, 15), padx=20)
        
        btn = ctk.CTkButton(popup, text="Understood", font=ctk.CTkFont(weight="bold"), fg_color=STATUS_RED_FG, hover_color="#b1142d", command=popup.destroy)
        btn.pack(pady=(0, 20))

    def update_status_bar_metrics(self):
        # Update Time
        self.time_lbl.configure(text=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        
        # Check DB
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("SELECT 1")
            conn.close()
            self.db_lbl.configure(text="🟢 DB: Connected")
        except:
            self.db_lbl.configure(text="🔴 DB: Error")
            
        # Check Cache Size
        total_size = 0
        if os.path.exists(TEMP_FOLDER):
            for f in os.listdir(TEMP_FOLDER):
                fp = os.path.join(TEMP_FOLDER, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        
        size_mb = total_size / (1024 * 1024)
        if size_mb < 1:
            size_text = f"{total_size / 1024:.0f} KB"
        else:
            size_text = f"{size_mb:.1f} MB"
            
        self.cache_lbl.configure(text=f"🧹 Temp Cache: {size_text}")
        
        self.after(5000, self.update_status_bar_metrics)

    def build_repository_pane(self, parent):
        self.repo_main_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        self.repo_main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.repo_main_frame.grid_columnconfigure(0, weight=1)
        self.repo_main_frame.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.repo_main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        header = ctk.CTkLabel(header_frame, text="Document Repository", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header_frame, text="🔄 Refresh", width=100, fg_color=PRIMARY_BLUE, command=self.load_repository_data)
        refresh_btn.pack(side="right")

        # Data Table Container
        table_container = ctk.CTkFrame(self.repo_main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        self.repo_table_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.repo_table_scroll.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        for i in range(5):
            self.repo_table_scroll.grid_columnconfigure(i, weight=1)

    def load_repository_data(self):
        for widget in self.repo_table_scroll.winfo_children():
            widget.destroy()
            
        cols = ["ID", "Format ID", "Revision", "File Path", "Status"]
        for i, text in enumerate(cols):
            lbl = ctk.CTkLabel(self.repo_table_scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
            lbl.grid(row=0, column=i, sticky="ew", pady=(10, 10))
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, format_id, revision, file_path, status FROM documents ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            lbl = ctk.CTkLabel(self.repo_table_scroll, text="No documents found.", text_color=TEXT_SECONDARY)
            lbl.grid(row=1, column=0, columnspan=5, pady=20)
            return

        for i, row in enumerate(rows):
            row_idx = i + 1
            lbl_id = ctk.CTkLabel(self.repo_table_scroll, text=str(row[0]), text_color=TEXT_PRIMARY)
            lbl_id.grid(row=row_idx, column=0, pady=5, padx=5)
            
            lbl_fmt = ctk.CTkLabel(self.repo_table_scroll, text=row[1], text_color=TEXT_PRIMARY)
            lbl_fmt.grid(row=row_idx, column=1, pady=5, padx=5)
            
            lbl_rev = ctk.CTkLabel(self.repo_table_scroll, text=row[2], text_color=TEXT_PRIMARY)
            lbl_rev.grid(row=row_idx, column=2, pady=5, padx=5)
            
            file_name = os.path.basename(row[3])
            lbl_path = ctk.CTkLabel(self.repo_table_scroll, text=file_name, text_color=TEXT_PRIMARY, cursor="hand2")
            lbl_path.grid(row=row_idx, column=3, pady=5, padx=5)
            
            # Double-click to open
            def open_pdf(e, path=row[3]):
                try: os.startfile(path)
                except Exception as ex: self.log_error("Open PDF Failed", str(ex))
            
            lbl_fmt.bind("<Double-1>", open_pdf)
            lbl_rev.bind("<Double-1>", open_pdf)
            lbl_path.bind("<Double-1>", open_pdf)
            
            status = row[4]
            bg, fg = STATUS_GRAY_BG, STATUS_GRAY_FG
            if status == "ACTIVE": bg, fg = STATUS_GREEN_BG, STATUS_GREEN_FG
            elif status == "INACTIVE": bg, fg = STATUS_RED_BG, STATUS_RED_FG
                
            badge_frame = ctk.CTkFrame(self.repo_table_scroll, fg_color=bg, corner_radius=10)
            badge_frame.grid(row=row_idx, column=4, pady=5, padx=5)
            badge_lbl = ctk.CTkLabel(badge_frame, text=status, text_color=fg, font=ctk.CTkFont(size=10, weight="bold"))
            badge_lbl.pack(padx=10, pady=2)

    def log_audit(self, user, action, details):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO audit_log (timestamp, user, action, details) VALUES (?, ?, ?, ?)", (now, user, action, details))
        conn.commit()
        conn.close()

    def log_print_history(self, batch_no, format_id, revision, copies_info, status):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO print_history (batch_no, format_id, revision, copies_info, print_date, status) VALUES (?, ?, ?, ?, ?, ?)", 
                       (batch_no, format_id, revision, copies_info, now, status))
        conn.commit()
        conn.close()

    def log_error(self, title, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error_logs.insert(0, {"timestamp": now, "title": title, "message": message})
        if getattr(self, 'current_pane', None) == "⚠️ Error Log":
            self.load_error_log_data()

    def cleanup_old_logs(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Clean up old print history (1 day) and audit logs (15 days)
        one_day_ago_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("DELETE FROM print_history WHERE print_date < ?", (one_day_ago_str,))
        
        fifteen_days_ago = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("DELETE FROM audit_log WHERE timestamp < ?", (fifteen_days_ago,))
        
        # 2. Clean up obsolete documents (2 days)
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT id, file_path FROM documents WHERE status='INACTIVE' AND inactive_date < ?", (two_days_ago,))
        obsolete_docs = cursor.fetchall()
        
        for doc_id, file_path in obsolete_docs:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting obsolete document {file_path}: {e}")
            cursor.execute("DELETE FROM documents WHERE id=?", (doc_id,))
            
        conn.commit()
        conn.close()
        
        # 3. Clean up the temp folder (1 day)
        one_day_ago = time.time() - (24 * 60 * 60)
        for filename in os.listdir(TEMP_FOLDER):
            if filename.endswith(".pdf"):
                file_path = os.path.join(TEMP_FOLDER, filename)
                try:
                    if os.path.getmtime(file_path) < one_day_ago:
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting temp file {file_path}: {e}")

    def build_qa_rejections_pane(self, parent):
        pane = QARejectionsPane(parent, self)
        pane.grid(row=0, column=0, sticky="nsew")

    def build_print_history_pane(self, parent):
        main_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header = ctk.CTkLabel(header_frame, text="Print History", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.pack(side="left")
        r_text = " Refresh" if self.icon_refresh else "🔄 Refresh"
        refresh_btn = ctk.CTkButton(header_frame, text=r_text, image=self.icon_refresh, width=100, fg_color=PRIMARY_BLUE, command=self.load_print_history_data)
        refresh_btn.pack(side="right")

        table_container = ctk.CTkFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        self.ph_table_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.ph_table_scroll.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        for i in range(6): self.ph_table_scroll.grid_columnconfigure(i, weight=1)

    def load_print_history_data(self):
        for widget in self.ph_table_scroll.winfo_children(): widget.destroy()
        cols = ["Batch ID", "Format ID", "Rev", "Copies Info", "Print Date", "Status"]
        for i, text in enumerate(cols):
            lbl = ctk.CTkLabel(self.ph_table_scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
            lbl.grid(row=0, column=i, sticky="ew", pady=(10, 10))
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT batch_no, format_id, revision, copies_info, print_date, status FROM print_history ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            lbl = ctk.CTkLabel(self.ph_table_scroll, text="No print history available.", text_color=TEXT_SECONDARY)
            lbl.grid(row=1, column=0, columnspan=6, pady=20)
            return

        for i, row in enumerate(rows):
            row_idx = i + 1
            for j in range(5):
                val = str(row[j]) if row[j] else "N/A"
                if j == 0 and len(val) > 20:
                    val = val[:17] + "..."
                lbl = ctk.CTkLabel(self.ph_table_scroll, text=val, text_color=TEXT_PRIMARY)
                lbl.grid(row=row_idx, column=j, pady=5, padx=5)
            
            status = row[5]
            bg, fg = STATUS_GRAY_BG, STATUS_GRAY_FG
            if status == "SUCCESS": bg, fg = STATUS_GREEN_BG, STATUS_GREEN_FG
            elif status == "ERROR": bg, fg = STATUS_RED_BG, STATUS_RED_FG
            
            badge_frame = ctk.CTkFrame(self.ph_table_scroll, fg_color=bg, corner_radius=10)
            badge_frame.grid(row=row_idx, column=5, pady=5, padx=5)
            badge_lbl = ctk.CTkLabel(badge_frame, text=status, text_color=fg, font=ctk.CTkFont(size=10, weight="bold"))
            badge_lbl.pack(padx=10, pady=2)

    def build_audit_log_pane(self, parent):
        main_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header = ctk.CTkLabel(header_frame, text="Audit Log (Last 15 Days)", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.pack(side="left")
        r_text = " Refresh" if self.icon_refresh else "🔄 Refresh"
        refresh_btn = ctk.CTkButton(header_frame, text=r_text, image=self.icon_refresh, width=100, fg_color=PRIMARY_BLUE, command=self.load_audit_log_data)
        refresh_btn.pack(side="right")

        table_container = ctk.CTkFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        table_container.grid(row=1, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        self.al_table_scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.al_table_scroll.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        for i in range(4): self.al_table_scroll.grid_columnconfigure(i, weight=1)

    def load_audit_log_data(self):
        for widget in self.al_table_scroll.winfo_children(): widget.destroy()
        cols = ["Timestamp", "User", "Action", "Details"]
        for i, text in enumerate(cols):
            lbl = ctk.CTkLabel(self.al_table_scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
            lbl.grid(row=0, column=i, sticky="ew", pady=(10, 10))
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, user, action, details FROM audit_log ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            lbl = ctk.CTkLabel(self.al_table_scroll, text="No audit logs available.", text_color=TEXT_SECONDARY)
            lbl.grid(row=1, column=0, columnspan=4, pady=20)
            return

        for i, row in enumerate(rows):
            row_idx = i + 1
            for j, val in enumerate(row):
                lbl = ctk.CTkLabel(self.al_table_scroll, text=str(val), text_color=TEXT_PRIMARY, anchor="w", justify="left", wraplength=250 if j==3 else 0)
                lbl.grid(row=row_idx, column=j, sticky="w", pady=8, padx=5)

    def build_error_log_pane(self, parent):
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header = ctk.CTkLabel(header_frame, text="Error Log", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.pack(side="left")
        
        clear_btn = ctk.CTkButton(header_frame, text="Clear Logs", width=100, fg_color="#D9534F", hover_color="#C9302C", command=self.clear_error_logs)
        clear_btn.pack(side="right")

        self.el_scroll = ctk.CTkScrollableFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        self.el_scroll.grid(row=1, column=0, sticky="nsew")
        self.el_scroll.grid_columnconfigure(0, weight=1)

    def load_error_log_data(self):
        for widget in self.el_scroll.winfo_children():
            widget.destroy()
            
        if not self.error_logs:
            lbl = ctk.CTkLabel(self.el_scroll, text="No errors recorded in this session.", text_color=TEXT_SECONDARY)
            lbl.grid(row=0, column=0, pady=20)
            return
            
        for i, log in enumerate(self.error_logs):
            card = ctk.CTkFrame(self.el_scroll, fg_color=BG_COLOR, corner_radius=8)
            card.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)
            
            icon = ctk.CTkLabel(card, text="⚠️", font=ctk.CTkFont(size=24), text_color="#D9534F")
            icon.grid(row=0, column=0, rowspan=2, padx=(10, 15), pady=10)
            
            title_frame = ctk.CTkFrame(card, fg_color="transparent")
            title_frame.grid(row=0, column=1, sticky="ew", pady=(10, 0))
            
            title = ctk.CTkLabel(title_frame, text=log["title"], font=ctk.CTkFont(weight="bold"), text_color="#D9534F")
            title.pack(side="left")
            
            timestamp = ctk.CTkLabel(title_frame, text=log["timestamp"], font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY)
            timestamp.pack(side="right", padx=(0, 10))
            
            msg = ctk.CTkLabel(card, text=log["message"], text_color=TEXT_PRIMARY, justify="left", wraplength=700)
            msg.grid(row=1, column=1, sticky="w", pady=(0, 10))

    def clear_error_logs(self):
        self.error_logs = []
        self.load_error_log_data()

    def build_settings_pane(self, parent):
        main_frame = ctk.CTkScrollableFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        header = ctk.CTkLabel(main_frame, text="System Settings", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.pack(anchor="w", pady=(0, 20))
        
        wm_frame = ctk.CTkFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        wm_frame.pack(fill="x", pady=10)
        
        lbl = ctk.CTkLabel(wm_frame, text="Global Watermark Text", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        entry = ctk.CTkEntry(wm_frame, textvariable=self.watermark_text, width=300)
        entry.pack(anchor="w", padx=20, pady=5)
        
        gh_lbl = ctk.CTkLabel(wm_frame, text="GitHub Auto-Updater Repo (e.g., username/repo)", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        gh_lbl.pack(anchor="w", padx=20, pady=(15, 5))
        
        gh_entry = ctk.CTkEntry(wm_frame, textvariable=self.github_repo, width=300, placeholder_text="e.g., myorg/myrepo")
        gh_entry.pack(anchor="w", padx=20, pady=5)
        
        lbl2 = ctk.CTkLabel(wm_frame, text="Watermark Appearance", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        lbl2.pack(anchor="w", padx=20, pady=(15, 5))
        
        app_frame = ctk.CTkFrame(wm_frame, fg_color="transparent")
        app_frame.pack(fill="x", padx=20, pady=5)
        
        lbl_size = ctk.CTkLabel(app_frame, text="Size:", text_color=TEXT_SECONDARY)
        lbl_size.pack(side="left", padx=(0, 5))
        size_drop = ctk.CTkOptionMenu(app_frame, values=[str(i) for i in range(9, 21)], variable=ctk.StringVar(value=str(self.watermark_fontsize.get())), command=lambda v: [self.watermark_fontsize.set(int(v)), self.refresh_preview()], width=80)
        size_drop.pack(side="left", padx=(0, 10))
        
        lbl_font = ctk.CTkLabel(app_frame, text="Font:", text_color=TEXT_SECONDARY)
        lbl_font.pack(side="left", padx=(0, 5))
        font_drop = ctk.CTkOptionMenu(app_frame, values=["Arial", "Helvetica", "Times New Roman", "Courier"], variable=self.watermark_fontname, command=lambda _: self.refresh_preview(), width=120)
        font_drop.pack(side="left", padx=(0, 20))
        
        lbl_op = ctk.CTkLabel(app_frame, text="Opacity:", text_color=TEXT_SECONDARY)
        lbl_op.pack(side="left", padx=(0, 5))
        op_slider = ctk.CTkSlider(app_frame, from_=0.1, to=1.0, number_of_steps=90, variable=self.watermark_opacity, command=self.refresh_preview, width=150)
        op_slider.pack(side="left", padx=(0, 20))
        
        lbl_jump = ctk.CTkLabel(app_frame, text="Pixel Jump:", text_color=TEXT_SECONDARY)
        lbl_jump.pack(side="left", padx=(0, 5))
        j_drop = ctk.CTkOptionMenu(app_frame, values=["1", "5", "10", "20", "50"], width=60, command=lambda v: self.watermark_pixel_jump.set(int(v)))
        j_drop.set("5")
        j_drop.pack(side="left")

        lbl3 = ctk.CTkLabel(wm_frame, text="Watermark Position", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        lbl3.pack(anchor="w", padx=20, pady=(15, 5))
        
        pos_frame = ctk.CTkFrame(wm_frame, fg_color="transparent")
        pos_frame.pack(anchor="w", padx=20, pady=(0, 20))
        
        u_btn = ctk.CTkButton(pos_frame, text="▲", width=30, height=30, command=lambda: self.move_watermark(0, -1))
        u_btn.grid(row=0, column=1, pady=2)
        l_btn = ctk.CTkButton(pos_frame, text="◀", width=30, height=30, command=lambda: self.move_watermark(-1, 0))
        l_btn.grid(row=1, column=0, padx=2)
        r_btn = ctk.CTkButton(pos_frame, text="▶", width=30, height=30, command=lambda: self.move_watermark(1, 0))
        r_btn.grid(row=1, column=2, padx=2)
        d_btn = ctk.CTkButton(pos_frame, text="▼", width=30, height=30, command=lambda: self.move_watermark(0, 1))
        d_btn.grid(row=2, column=1, pady=2)
        
        print_frame = ctk.CTkFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        print_frame.pack(fill="x", pady=10)
        
        lbl_print = ctk.CTkLabel(print_frame, text="Printing Preferences", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        lbl_print.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.silent_print_switch = ctk.CTkSwitch(print_frame, text="Enable Direct Printing (Bypass Print Dialog)", variable=self.silent_print_var, command=self.toggle_printer_dropdown)
        self.silent_print_switch.pack(anchor="w", padx=20, pady=5)
        
        try:
            import win32print
            printers = [p[2] for p in win32print.EnumPrinters(2)]
        except:
            printers = []
        if not printers: printers = ["No printers found"]
        
        lbl_printer = ctk.CTkLabel(print_frame, text="Select Printer (A4 Only):", text_color=TEXT_SECONDARY)
        lbl_printer.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.printer_dropdown = ctk.CTkOptionMenu(print_frame, values=printers, variable=self.selected_printer_var, state="disabled", width=300)
        self.printer_dropdown.pack(anchor="w", padx=20, pady=(5, 20))
        if printers and printers[0] != "No printers found": 
            self.selected_printer_var.set(printers[0])
        
        cache_frame = ctk.CTkFrame(main_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        cache_frame.pack(fill="x", pady=10)
        
        lbl_cache = ctk.CTkLabel(cache_frame, text="Storage & Cache Management", font=ctk.CTkFont(weight="bold"), text_color=TEXT_PRIMARY)
        lbl_cache.pack(anchor="w", padx=20, pady=(15, 5))
        
        desc_cache = ctk.CTkLabel(cache_frame, text="Clear temporary files to instantly free up disk space.", text_color=TEXT_SECONDARY)
        desc_cache.pack(anchor="w", padx=20, pady=5)
        
        btn_clear = ctk.CTkButton(cache_frame, text="🗑️ Clear Temp Cache Now", fg_color=STATUS_RED_BG, hover_color=STATUS_RED_FG, text_color="white", command=self.clear_temp_cache)
        btn_clear.pack(anchor="w", padx=20, pady=(5, 20))

    def toggle_printer_dropdown(self):
        if self.silent_print_var.get():
            self.printer_dropdown.configure(state="normal")
        else:
            self.printer_dropdown.configure(state="disabled")

    def clear_temp_cache(self):
        cleared = 0
        if os.path.exists(TEMP_FOLDER):
            for f in os.listdir(TEMP_FOLDER):
                try:
                    fp = os.path.join(TEMP_FOLDER, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
                        cleared += 1
                except Exception as e:
                    print("Error deleting cache file:", e)
        self.show_status_msg(f"Cleared {cleared} temporary files")
        self.update_status_bar_metrics()

    def build_about_pane(self, parent):
        main_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkLabel(main_frame, text="About & Help", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
        header.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        tabview = ctk.CTkTabview(main_frame, fg_color="transparent")
        tabview.grid(row=1, column=0, sticky="nsew")
        
        tab_info = tabview.add("Information")
        tab_tour = tabview.add("How to Use (Tour)")
        
        # --- Information Tab ---
        card = ctk.CTkFrame(tab_info, fg_color=CARD_BG, corner_radius=15, border_color=BORDER_COLOR, border_width=1)
        card.pack(fill="both", expand=True, padx=40, pady=40)
        
        title = ctk.CTkLabel(card, text="Controlled Print System", font=ctk.CTkFont(size=32, weight="bold"), text_color="#0b63d6")
        title.pack(pady=(40, 5))
        
        version = ctk.CTkLabel(card, text=f"Version {APP_VERSION}", font=ctk.CTkFont(size=14, weight="bold"), fg_color="#eef5ff", text_color="#0b63d6", corner_radius=10)
        version.pack(pady=5, ipadx=10, ipady=4)
        
        desc = ctk.CTkLabel(card, text="A centralized enterprise system for the QA department to manage, track, and securely print controlled copies of master PDF documents.", wraplength=450, font=ctk.CTkFont(size=15), text_color=TEXT_SECONDARY)
        desc.pack(pady=20)
        
        dev_frame = ctk.CTkFrame(card, fg_color="#f9fbfd", corner_radius=10, border_color="#dbe2ea", border_width=1)
        dev_frame.pack(pady=10, padx=60, fill="x")
        
        ctk.CTkLabel(dev_frame, text="👨‍💻 Developer", font=ctk.CTkFont(size=13), text_color=TEXT_SECONDARY).pack(pady=(15, 0))
        ctk.CTkLabel(dev_frame, text="P.L.Sai Kaushik", font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_PRIMARY).pack(pady=(0, 15))

        dev_team = ctk.CTkLabel(card, text="Designed & Developed by SITE - III QA Team", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY)
        dev_team.pack(pady=(20, 5))

        contact = ctk.CTkLabel(card, text="Support: qavizg@molbiodiagnostics.com", font=ctk.CTkFont(size=13), text_color=PRIMARY_BLUE)
        contact.pack(pady=5)
        
        copy = ctk.CTkLabel(card, text="© 2026 All rights reserved to QA Team SITE-III", font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY)
        copy.pack(side="bottom", pady=30)
        
        # --- How to Use (Tour) Tab ---
        tour_scroll = ctk.CTkScrollableFrame(tab_tour, fg_color="transparent")
        tour_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        steps = [
            ("📂 Step 1: Upload to Repository", "Go to the Document Repository tab. Click 'Upload PDFs' and select your master files. Ensure files are named exactly like FORMATID-REVISION.pdf (e.g., DOC123-01.pdf)."),
            ("⚙️ Step 2: Configure Settings", "Head over to the Settings tab. Choose your preferred watermark font, size, and layout offset. Your choices will automatically save!"),
            ("📋 Step 3: Paste Batch Data", "Copy your raw data from Excel. Go to the Batch Print tab and paste it directly into the text box on the right. You can safely paste thousands of rows at once!"),
            ("✨ Step 4: Process and Review", "Click the 'Process Data' button. The software will intelligently read your data and format the pages and copies. Click on any row to instantly see a live preview of the generated watermark."),
            ("🖨️ Step 5: Print Controlled Copies", "Once everything looks perfect, click 'Print All Pending'. The system will generate the dynamic diagonal watermark on every required page and send them seamlessly to your selected printer!"),
            ("⚠️ Step 6: Check the Error Log", "If any document is missing or printing fails, the system will log exactly what happened. Check the Error Log tab for detailed diagnostics.")
        ]
        
        for i, (stitle, sdesc) in enumerate(steps):
            scard = ctk.CTkFrame(tour_scroll, fg_color=CARD_BG, corner_radius=8, border_color=BORDER_COLOR, border_width=1)
            scard.pack(fill="x", pady=5)
            
            lbl_title = ctk.CTkLabel(scard, text=stitle, font=ctk.CTkFont(size=16, weight="bold"), text_color=PRIMARY_BLUE)
            lbl_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            lbl_desc = ctk.CTkLabel(scard, text=sdesc, text_color=TEXT_PRIMARY, wraplength=700, justify="left")
            lbl_desc.pack(anchor="w", padx=15, pady=(0, 15))

    # ==========================================
    # LOGIC
    # ==========================================

    def parse_copies_info(self, info_str):
        info_str = str(info_str).strip()
        if info_str.isdigit(): return [{'page': None, 'copies': int(info_str)}]
        
        # Merge dangling copies (e.g. "01") onto the previous line to handle Excel wrapping
        import re
        info_str = re.sub(r'\n\s*(?=\d+\s*(?:\n|$))', ' ', info_str)
        
        # Standardize separators
        info_str = info_str.replace(',', '\n')
        lines = [line.strip() for line in info_str.split('\n') if line.strip()]
        
        results = []
        current_pages = []
        
        for line in lines:
            import re
            clean_line = re.sub(r'(?i)\s*of\s*\d+', '', line)
            
            copies = None
            m_copies = re.search(r'(\d+)\s*cop', clean_line, re.IGNORECASE)
            if m_copies:
                copies = int(m_copies.group(1))
                clean_line = clean_line[:m_copies.start()]
            else:
                m_num = re.search(r'\s*(\d+)\s*$', clean_line)
                if m_num:
                    copies = int(m_num.group(1))
                    clean_line = clean_line[:m_num.start()]
                    
            nums = [int(x) for x in re.findall(r'\d+', clean_line)]
            pages = []
            if re.search(r'(?i)\bto\b|-', clean_line) and len(nums) >= 2:
                start = nums[0]
                end = nums[-1]
                pages = list(range(start, end + 1))
            elif re.search(r'(?i)\band\b', clean_line) and len(nums) >= 2:
                pages = nums
            elif len(nums) > 0:
                pages = nums
                
            if pages:
                current_pages.extend(pages)
                
            if copies is not None:
                if not current_pages:
                    results.append({'page': None, 'copies': copies})
                else:
                    for p in current_pages:
                        results.append({'page': p, 'copies': copies})
                current_pages = []
                
        if current_pages:
            for p in current_pages:
                results.append({'page': p, 'copies': 1})
                
        if not results: results.append({'page': None, 'copies': 1})
        return results

    def format_copies_summary(self, parsed_info):
        if not parsed_info: return ""
        if len(parsed_info) == 1 and parsed_info[0]['page'] is None:
            return f"All ({parsed_info[0]['copies']}x)"
            
        parts = []
        for item in parsed_info:
            parts.append(f"Pg {item['page']} ({item['copies']}x)")
            
        if len(parts) > 3:
            return ", ".join(parts[:3]) + f" ... (+{len(parts)-3})"
        return ", ".join(parts)

    def upload_document(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not file_paths: return
        
        success_count = 0
        error_msgs = []
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            import re
            m = re.match(r'^(FM.*?)\s*-\s*(\d{2})$', name_without_ext, flags=re.IGNORECASE)
            
            if not m:
                error_txt = f"Invalid filename: '{filename}'\n\nRules:\n1. Must start with 'FM'\n2. Must end with ' - ' followed by exactly 2 digits for the revision (e.g., '00', '01').\n\nDescriptive names or other prefixes (SOP, STP) are not allowed."
                self.log_error("Upload Failed", error_txt)
                error_msgs.append(f"{filename}: Invalid format")
                continue
            
            format_part = m.group(1).strip()
            revision = m.group(2)
            format_id = format_part.replace("-", "/").upper()
            destination = os.path.join(REPOSITORY, filename)
            
            try:
                shutil.copy(file_path, destination)
            except shutil.SameFileError:
                pass
            except Exception as e:
                self.log_error("Upload Error", f"Failed to copy file '{filename}': {str(e)}")
                error_msgs.append(f"{filename}: Copy failed")
                continue
            
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE documents SET status='INACTIVE', inactive_date=? WHERE format_id=?", (now, format_id))
                cursor.execute("INSERT INTO documents (format_id, revision, file_path, status) VALUES (?, ?, ?, ?)", (format_id, revision, destination, "ACTIVE"))
                success_count += 1
                self.log_audit("admin", "UPLOAD_DOCUMENT", f"Uploaded master PDF: {format_id} Rev {revision}")
            except Exception as e:
                self.log_error("Database Error", f"Failed to update database for '{filename}': {str(e)}")
                error_msgs.append(f"{filename}: DB Error")
            
        conn.commit()
        conn.close()
        self.load_repository_data()
        
        if success_count > 0 and not error_msgs:
            self.show_status_msg(f"Uploaded {success_count} document(s) successfully.")
        elif success_count > 0 and error_msgs:
            self.show_status_msg(f"Uploaded {success_count} docs. {len(error_msgs)} failed (Invalid Name Format).", is_error=True)
        elif not success_count and error_msgs:
            self.show_status_msg(f"Upload failed: Invalid Name Format", is_error=True)

    def clear_queue(self):
        self.parsed_logs = []
        self.render_table()
        
        # Clear the pasted text box
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Paste Excel batch log here...")
        
        # Close any open preview document
        self.current_preview_log = None
        self.toggle_right_pane()
        if hasattr(self, 'preview_image_label'):
            self.preview_image_label.configure(image="", text="Select a document to preview.")
            
        self.show_status_msg("All data and previews cleared", duration=2000)

    def process_log(self):
        import urllib.request
        import json
        url = "https://script.google.com/macros/s/AKfycbzJAtz2MktkFtBL1EKO2kWWXANvSNCTEkvSLHPVieR_qDTylxrtN1zT6tlorSrTVwF48w/exec"
        payload = {"action": "checkLicense", "machineId": getattr(self, 'machine_id', 'UNKNOWN'), "username": getattr(self, 'username', 'UNKNOWN')}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                if res_data.get("status") != "active":
                    for widget in self.winfo_children():
                        widget.destroy()
                    self.build_blocked_screen()
                    return
        except Exception:
            for widget in self.winfo_children():
                widget.destroy()
            self.build_blocked_screen(offline=True)
            return

        raw_data = self.log_text.get("1.0", "end").strip()
        if not raw_data: return
        reader = csv.reader(io.StringIO(raw_data), dialect='excel-tab')
        valid_logs = []
        for cols in reader:
            try:
                if not cols: continue
                joined_cols = " ".join([str(c).upper() for c in cols])
                if "FORMAT ID" in joined_cols and "REVISION" in joined_cols:
                    continue
                    
                if len(cols) >= 7 and "BATCH ID" not in joined_cols:
                    batch_no = str(cols[0]).replace('\n', '').replace('\r', '').strip().upper()
                    format_id = str(cols[4]).strip().upper()
                    revision = str(cols[5]).strip().zfill(2).upper()
                    parsed_copies = self.parse_copies_info(cols[6])
                elif len(cols) == 3:
                    batch_no = None
                    format_id = str(cols[0]).strip().upper()
                    revision = str(cols[1]).strip().zfill(2).upper()
                    parsed_copies = self.parse_copies_info(cols[2])
                else:
                    continue
                
                # (Removed invalid null page check here to allow full-document printing)
                    
                valid_logs.append({
                    "id": len(valid_logs) + 1,
                    "batch_no": batch_no,
                    "format_id": format_id,
                    "revision": revision,
                    "summary": self.format_copies_summary(parsed_copies),
                    "status": "PENDING",
                    "parsed_copies": parsed_copies,
                    "rotation": 0
                })
            except Exception as e:
                error_msg = str(e)
                self.log_error("Data Format Issue", error_msg)
                self.show_modern_error("Formatting Issue", error_msg)
                
        self.parsed_logs = valid_logs
        self.render_table()
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Paste Excel batch log here...")
        self.show_status_msg(f"Processed {len(self.parsed_logs)} logs", duration=3)

    def rotate_preview(self):
        if hasattr(self, 'current_preview_log') and self.current_preview_log:
            self.current_preview_log['rotation'] = (self.current_preview_log.get('rotation', 0) + 90) % 360
            self.preview_document(self.current_preview_log)

    def render_table(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
            
        cols = ["#", "Batch ID", "Format ID", "Revision", "Pages/Copies", "Status", "Action"]
        for i, text in enumerate(cols):
            lbl = ctk.CTkLabel(self.table_scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
            lbl.grid(row=0, column=i, sticky="ew", pady=(0, 10))
        
        total = len(self.parsed_logs)
        pending = sum(1 for log in self.parsed_logs if log['status'] == "PENDING")
        printed = sum(1 for log in self.parsed_logs if log['status'] == "PRINTED")
        errors = sum(1 for log in self.parsed_logs if log['status'] == "ERROR")
        
        self.stat_total.configure(text=f"Total: {total}")
        self.stat_pending.configure(text=f"Pending: {pending}")
        self.stat_printed.configure(text=f"Printed: {printed}")
        self.stat_error.configure(text=f"Error: {errors}")
        
        if total > 0:
            self.print_all_btn.configure(text=f"🖨️ Print {total} Documents")
        else:
            self.print_all_btn.configure(text="🖨️ Print Pending")

        for i, log in enumerate(self.parsed_logs):
            row_idx = i + 1
            
            lbl_id = ctk.CTkLabel(self.table_scroll, text=str(log['id']), text_color=TEXT_PRIMARY)
            lbl_id.grid(row=row_idx, column=0, pady=5, padx=5)
            
            b_text = log['batch_no'] if log['batch_no'] else "N/A"
            if len(b_text) > 20: b_text = b_text[:17] + "..."
            lbl_batch = ctk.CTkLabel(self.table_scroll, text=b_text, text_color=TEXT_PRIMARY)
            lbl_batch.grid(row=row_idx, column=1, pady=5, padx=5)
            
            lbl_fmt = ctk.CTkLabel(self.table_scroll, text=log['format_id'], text_color=TEXT_PRIMARY)
            lbl_fmt.grid(row=row_idx, column=2, pady=5, padx=5)
            
            lbl_rev = ctk.CTkLabel(self.table_scroll, text=log['revision'], text_color=TEXT_PRIMARY)
            lbl_rev.grid(row=row_idx, column=3, pady=5, padx=5)
            
            lbl_pg = ctk.CTkLabel(self.table_scroll, text=log['summary'], text_color=TEXT_PRIMARY)
            lbl_pg.grid(row=row_idx, column=4, pady=5, padx=5)

            status = log['status']
            bg, fg = STATUS_GRAY_BG, STATUS_GRAY_FG
            if status == "PRINTED": bg, fg = STATUS_GREEN_BG, STATUS_GREEN_FG
            elif status == "ERROR": bg, fg = STATUS_RED_BG, STATUS_RED_FG
                
            badge_frame = ctk.CTkFrame(self.table_scroll, fg_color=bg, corner_radius=10)
            badge_frame.grid(row=row_idx, column=5, pady=5, padx=5)
            badge_lbl = ctk.CTkLabel(badge_frame, text=status, text_color=fg, font=ctk.CTkFont(size=10, weight="bold"))
            badge_lbl.pack(padx=10, pady=2)

            action_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            action_frame.grid(row=row_idx, column=6, pady=5, padx=5)
            
            v_text = "" if self.icon_eye else "👁️"
            p_text = "" if self.icon_print else "🖨️"
            
            btn_view = ctk.CTkButton(action_frame, text=v_text, image=self.icon_eye, width=30, height=30, fg_color="#555555", hover_color="#777777", corner_radius=5, text_color=TEXT_PRIMARY, command=lambda l=log: self.preview_document(l))
            btn_view.pack(side="left", padx=2)
            btn_print = ctk.CTkButton(action_frame, text=p_text, image=self.icon_print, width=30, height=30, fg_color=PRIMARY_BLUE, hover_color="#2b6b94", corner_radius=5, text_color=TEXT_PRIMARY, command=lambda l=log: self.print_document(l))
            btn_print.pack(side="left", padx=2)
            
            d_text = "" if self.icon_delete else "🗑️"
            btn_delete = ctk.CTkButton(action_frame, text=d_text, image=self.icon_delete, width=30, height=30, fg_color="#D9534F", hover_color="#C9302C", corner_radius=5, text_color=TEXT_PRIMARY, command=lambda idx=i: self.remove_log_entry(idx))
            btn_delete.pack(side="left", padx=2)

    def remove_log_entry(self, index):
        if 0 <= index < len(self.parsed_logs):
            del self.parsed_logs[index]
            self.render_table()

    def get_master_pdf_path(self, format_id, revision):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM documents WHERE format_id=? AND revision=? AND status='ACTIVE'", (format_id, revision))
        result = cursor.fetchone()
        conn.close()
        if not result: return None
        return os.path.join(REPOSITORY, os.path.basename(result[0]))

    def get_shift_date(self):
        now = datetime.now()
        if now.hour < 6:
            shift_date = now - timedelta(days=1)
        else:
            shift_date = now
        return shift_date.strftime("%d/%m/%Y")

    def preview_document(self, log, force_refresh=False):
        if not force_refresh and getattr(self, 'current_preview_log', None) == log:
            # Toggle off
            self.preview_image_label.configure(image="", text="Select a document to preview.")
            self.current_preview_log = None
            self.toggle_right_pane()
            self.show_status_msg("Preview closed", duration=2)
            return

        self.current_preview_log = log
        pdf_path = self.get_master_pdf_path(log['format_id'], log['revision'])
        if not pdf_path or not os.path.exists(pdf_path):
            self.preview_image_label.configure(image="", text="[ DOCUMENT NOT AVAILABLE ]\nPlease upload the master file to the Repository.")
            self.show_status_msg(f"Master PDF not found for {log['format_id']} Rev {log['revision']}", is_error=True)
            return

        timestamp = datetime.now().strftime("%H%M%S")
        watermark_pdf = os.path.join(TEMP_FOLDER, f"preview_wm_{timestamp}.pdf")
        
        try:
            preview_page = log['parsed_copies'][0]['page']
            
            original = fitz.open(pdf_path)
            
            page_idx = (preview_page - 1) if preview_page is not None else 0
            if page_idx >= len(original): page_idx = 0
            
            target_page = original[page_idx]
            
            new_doc = fitz.open()
            new_doc.insert_pdf(original, from_page=page_idx, to_page=page_idx)
            page = new_doc[0]
            
            rot = log.get('rotation', 0)
            if rot: page.set_rotation(page.rotation + rot)
            
            date_str = self.get_shift_date()
            batch_no = log['batch_no']
            
            base_fs = self.watermark_fontsize.get()
            if batch_no:
                wm_text = self.watermark_text.get()
                
                batch_lines = []
                if len(batch_no) > 35 and ',' in batch_no:
                    parts = batch_no.split(',')
                    half = (len(parts) + 1) // 2
                    batch_lines.append(",".join(parts[:half]) + ",")
                    batch_lines.append(",".join(parts[half:]))
                else:
                    batch_lines.append(batch_no)
                    
                # Dynamically scale font size based on string length, min 12
                scale_reduction = max(0, (len(batch_no) - 25) // 6)
                batch_fs = max(12, base_fs - scale_reduction)
                
                lines = [(f"{wm_text} {date_str}", batch_fs)]
                for bl in batch_lines:
                    lines.append((bl, batch_fs))
            else:
                lines = [(f"AUTHORISED COPY {date_str}", base_fs)]
                
            y_vis = page.rect.y1 - 10
            
            font_choice = self.watermark_fontname.get()
            try:
                if font_choice == "Arial":
                    w_font = fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf")
                    page.insert_font(fontname="w_font", fontfile="C:/Windows/Fonts/arial.ttf")
                elif font_choice == "Times New Roman":
                    w_font = fitz.Font(fontfile="C:/Windows/Fonts/times.ttf")
                    page.insert_font(fontname="w_font", fontfile="C:/Windows/Fonts/times.ttf")
                elif font_choice == "Courier":
                    w_font = fitz.Font("cour")
                else:
                    w_font = fitz.Font("helv")
                f_name = "w_font" if font_choice in ["Arial", "Times New Roman"] else ("cour" if font_choice == "Courier" else "helv")
            except:
                w_font = fitz.Font("helv")
                f_name = "helv"
                
            for text, fs in reversed(lines):
                line_len = w_font.text_length(text, fontsize=fs)
                p_vis = fitz.Point(page.rect.x1 - 60 - line_len + self.watermark_x_offset.get(), y_vis + self.watermark_y_offset.get())
                p_unrot = p_vis * page.derotation_matrix
                text_rot = fitz.Matrix(page.rotation)
                page.insert_text(p_unrot, text, fontname=f_name, fontsize=fs, color=(0.5, 0.5, 0.5), fill_opacity=self.watermark_opacity.get(), morph=(p_unrot, text_rot))
                y_vis -= (fs + 4)
            
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            max_h = 500
            max_w = self.preview_image_label.winfo_width()
            if max_w < 100: max_w = 400 # Fallback
            
            # Add some padding margin
            max_w -= 20
            
            ratio_w = max_w / img.width
            ratio_h = max_h / img.height
            ratio = min(ratio_w, ratio_h)
            
            # Only downscale, don't upscale small images
            if ratio < 1.0:
                new_w = int(img.width * ratio)
                new_h = int(img.height * ratio)
            else:
                new_w = img.width
                new_h = img.height
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
            self.preview_image_label.configure(image=ctk_img, text="")
            self.toggle_right_pane()
            
            new_doc.close()
            original.close()
            self.show_status_msg(f"Previewing Batch {log['batch_no']}", duration=0)
        except Exception as e:
            self.show_status_msg(f"Preview Error: {str(e)}", is_error=True)

    def create_watermark(self, output_pdf, batch_no, width, height):
        c = canvas.Canvas(output_pdf, pagesize=(width, height))
        c.saveState()
        opacity = self.watermark_opacity.get()
        grey = Color(0.5, 0.5, 0.5, alpha=opacity)
        c.setFillColor(grey)
        
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            c.setFont("Arial", 18)
        except Exception:
            c.setFont("Helvetica", 18)

        date_str = self.get_shift_date()
        
        if batch_no:
            wm_text = self.watermark_text.get()
            lines = [
                f"{wm_text} {date_str}",
                f"{batch_no}"
            ]
        else:
            lines = [f"AUTHORISED COPY {date_str}"]
        
        x = width - 60
        y = 60
        
        for line in lines:
            c.drawRightString(x, y, line)
            y -= 20

        c.restoreState()
        c.save()

    def print_document(self, log):
        pdf_path = self.get_master_pdf_path(log['format_id'], log['revision'])
        if not pdf_path or not os.path.exists(pdf_path):
            self.log_error("Document Not Found", f"Format ID {log['format_id']} Rev {log['revision']} is missing from the master list.")
            log['status'] = "ERROR"
            self.render_table()
            return
            
        timestamp = datetime.now().strftime("%H%M%S")
        b_name = log['batch_no'] if log['batch_no'] else "AUTH"
        output_pdf = os.path.join(TEMP_FOLDER, f"{b_name}_{timestamp}.pdf")

        try:
            rot = log.get('rotation', 0)
            new_doc = self.generate_watermarked_doc(pdf_path, log['parsed_copies'], log['batch_no'], rot)
            new_doc.save(output_pdf)
            new_doc.close()
            if self.silent_print_var.get() and self.selected_printer_var.get() != "No printers found":
                import win32api
                win32api.ShellExecute(0, "printto", output_pdf, f'"{self.selected_printer_var.get()}"', ".", 0)
            else:
                os.startfile(output_pdf)
            log['status'] = "PRINTED"
            b_log = log['batch_no'] if log['batch_no'] else "N/A"
            self.log_print_history(b_log, log['format_id'], log['revision'], log['summary'], "SUCCESS")
            self.log_audit("admin", "PRINT_DOCUMENT", f"Printed Batch: {b_log}, Format: {log['format_id']}")
        except Exception as e:
            print("Print Error:", e)
            b_log = log['batch_no'] if log['batch_no'] else "N/A"
            self.log_error("Print Failed", f"An error occurred while printing {b_log} (Format ID {log['format_id']}): {str(e)}")
            log['status'] = "ERROR"
            self.log_print_history(b_log, log['format_id'], log['revision'], log['summary'], "ERROR")
            self.log_audit("admin", "PRINT_ERROR", f"Failed to print Batch: {b_log}")
        self.render_table()

    def print_all_pending(self):
        pending_logs = [log for log in self.parsed_logs if log['status'] == "PENDING"]
        if not pending_logs:
            self.show_status_msg("No pending documents to print", is_error=True)
            return
        
        total_pending = len(pending_logs)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=20)
        
        # Disable print button during printing
        if hasattr(self, 'print_all_btn'):
            self.print_all_btn.configure(state="disabled")

        def run_bulk_print():
            timestamp = datetime.now().strftime("%H%M%S")
            bulk_pdf_path = os.path.join(TEMP_FOLDER, f"BULK_PRINT_{timestamp}.pdf")
            master_bulk_doc = fitz.open()
            
            processed_any = False
            
            for index, log in enumerate(pending_logs):
                pdf_path = self.get_master_pdf_path(log['format_id'], log['revision'])
                b_log = log['batch_no'] if log['batch_no'] else "N/A"
                
                if not pdf_path or not os.path.exists(pdf_path):
                    log['status'] = "ERROR"
                    self.log_print_history(b_log, log['format_id'], log['revision'], log['summary'], "ERROR")
                    self.log_audit("admin", "PRINT_ERROR", f"Failed to print Batch: {b_log} (File not found)")
                    continue
                    
                try:
                    rot = log.get('rotation', 0)
                    new_doc = self.generate_watermarked_doc(pdf_path, log['parsed_copies'], log['batch_no'], rot)
                    master_bulk_doc.insert_pdf(new_doc)
                    new_doc.close()
                    log['status'] = "PRINTED"
                    self.log_print_history(b_log, log['format_id'], log['revision'], log['summary'], "SUCCESS")
                    self.log_audit("admin", "PRINT_DOCUMENT", f"Bulk Printed Batch: {b_log}, Format: {log['format_id']}")
                    processed_any = True
                except Exception as e:
                    self.log_error("Bulk Print Error", f"Batch {b_log} failed: {str(e)}")
                    log['status'] = "ERROR"
                    self.log_print_history(b_log, log['format_id'], log['revision'], log['summary'], "ERROR")
                    self.log_audit("admin", "PRINT_ERROR", f"Failed to bulk print Batch: {b_log}")
                
                progress = (index + 1) / total_pending
                
                def update_ui(p=progress, i=index):
                    self.progress_bar.set(p)
                    self.status_lbl.configure(text=f"⏳ Processing Bulk Print {i + 1}/{total_pending}...", text_color=STATUS_GREEN_FG)
                
                self.after(0, update_ui)
                    
            if processed_any:
                master_bulk_doc.save(bulk_pdf_path)
                master_bulk_doc.close()
                if self.silent_print_var.get() and self.selected_printer_var.get() != "No printers found":
                    try:
                        import win32api
                        win32api.ShellExecute(0, "printto", bulk_pdf_path, f'"{self.selected_printer_var.get()}"', ".", 0)
                    except Exception as e:
                        self.log_error("Printer Interface Error", f"Failed to send to printer. Check Adobe Acrobat: {str(e)}")
                        self.after(0, lambda: self.show_status_msg("Failed to send to printer. Check Error Log.", is_error=True))
                else:
                    try:
                        os.startfile(bulk_pdf_path)
                    except Exception as e:
                        self.log_error("File Open Error", f"Failed to open PDF. Install a PDF viewer: {str(e)}")
                self.after(0, lambda: self.show_status_msg("Bulk Print Complete"))
            else:
                master_bulk_doc.close()
                self.after(0, lambda: self.show_status_msg("System Ready", duration=0))
                
            def finish_print():
                self.progress_bar.pack_forget()
                if hasattr(self, 'print_all_btn'):
                    self.print_all_btn.configure(state="normal")
                self.render_table()
                
            self.after(0, finish_print)

        import threading
        threading.Thread(target=run_bulk_print, daemon=True).start()

    def generate_watermarked_doc(self, original_pdf, parsed_copies, batch_no, rotation=0):
        original = fitz.open(original_pdf)
        pages_to_include = []
        total_pages = len(original)
        
        for item in parsed_copies:
            copies = item['copies']
            page = item['page']
            if page is None:
                for _ in range(copies): pages_to_include.extend(range(total_pages))
            else:
                page_idx = page - 1
                if 0 <= page_idx < total_pages:
                    for _ in range(copies): pages_to_include.append(page_idx)
        
        new_doc = fitz.open()
        for idx in pages_to_include:
            new_doc.insert_pdf(original, from_page=idx, to_page=idx)
            
        date_str = self.get_shift_date()
        
        for page in new_doc:
            if rotation:
                page.set_rotation(page.rotation + rotation)
                
            base_fs = self.watermark_fontsize.get()
            if batch_no:
                wm_text = self.watermark_text.get()
                
                batch_lines = []
                if len(batch_no) > 35 and ',' in batch_no:
                    parts = batch_no.split(',')
                    half = (len(parts) + 1) // 2
                    batch_lines.append(",".join(parts[:half]) + ",")
                    batch_lines.append(",".join(parts[half:]))
                else:
                    batch_lines.append(batch_no)
                    
                # Dynamically scale font size based on string length, min 12
                scale_reduction = max(0, (len(batch_no) - 25) // 6)
                batch_fs = max(12, base_fs - scale_reduction)
                
                lines = [(f"{wm_text} {date_str}", batch_fs)]
                for bl in batch_lines:
                    lines.append((bl, batch_fs))
            else:
                lines = [(f"AUTHORISED COPY {date_str}", base_fs)]
                
            y_vis = page.rect.y1 - 10
            
            font_choice = self.watermark_fontname.get()
            try:
                if font_choice == "Arial":
                    w_font = fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf")
                    page.insert_font(fontname="w_font", fontfile="C:/Windows/Fonts/arial.ttf")
                elif font_choice == "Times New Roman":
                    w_font = fitz.Font(fontfile="C:/Windows/Fonts/times.ttf")
                    page.insert_font(fontname="w_font", fontfile="C:/Windows/Fonts/times.ttf")
                elif font_choice == "Courier":
                    w_font = fitz.Font("cour")
                else:
                    w_font = fitz.Font("helv")
                f_name = "w_font" if font_choice in ["Arial", "Times New Roman"] else ("cour" if font_choice == "Courier" else "helv")
            except:
                w_font = fitz.Font("helv")
                f_name = "helv"
                
            for text, fs in reversed(lines):
                line_len = w_font.text_length(text, fontsize=fs)
                p_vis = fitz.Point(page.rect.x1 - 60 - line_len + self.watermark_x_offset.get(), y_vis + self.watermark_y_offset.get())
                p_unrot = p_vis * page.derotation_matrix
                text_rot = fitz.Matrix(page.rotation)
                page.insert_text(p_unrot, text, fontname=f_name, fontsize=fs, color=(0.5, 0.5, 0.5), fill_opacity=self.watermark_opacity.get(), morph=(p_unrot, text_rot))
                y_vis -= (fs + 4)
            
        original.close()
        return new_doc

if __name__ == "__main__":
    # Force Windows to use our custom icon in the taskbar
    # THIS MUST RUN BEFORE CTK INITIALIZATION!
    try:
        import ctypes
        myappid = 'cdps.system.printing.2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print("Could not set taskbar icon:", e)
        
    app = ControlledPrintSystem()
    app.mainloop()
