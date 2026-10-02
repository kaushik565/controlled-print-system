import customtkinter as ctk
from tkinter import messagebox
import urllib.request
import json
import time
from datetime import datetime, timedelta

BG_COLOR = "#f4f7fb"
CARD_BG = "#ffffff"
BORDER_COLOR = "#dbe2ea"
TEXT_PRIMARY = "#1a1a1a"
TEXT_SECONDARY = "#607182"
PRIMARY_BLUE = "#0b63d6"
HOVER_BLUE = "#094faa"

INPUT_STYLE = {
    "height": 36,
    "corner_radius": 6,
    "border_width": 1,
    "border_color": "#c4d1eb",
    "fg_color": "#f9fbfd",
    "text_color": TEXT_PRIMARY
}

COMBO_STYLE = {
    "corner_radius": 5,
    "fg_color": "#f9fbfd",
    "text_color": TEXT_PRIMARY,
    "button_color": "#f9fbfd",
    "button_hover_color": "#e4ecf7",
    "dropdown_fg_color": "#ffffff",
    "dropdown_hover_color": "#f1f3f4",
    "dropdown_text_color": TEXT_PRIMARY
}

class QARejectionsPane(ctk.CTkFrame):
    def __init__(self, master, app_instance, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_instance
        self.configure(fg_color=BG_COLOR, corner_radius=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.rejection_items = []
        self.WEBHOOK_URL = "https://default717100838e2b4b17be10a1c62fd275.f6.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/ce0eb8527bf14e9ba11a17d8f9039bda/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=2a4V6gLSZbx1mYt4t3947ag4Pxos2EqrGpKfxGJt3aw"

        self.lookups = {
            "Shift": ["A-SHIFT", "B-SHIFT", "C-SHIFT", "GENERAL"],
            "LOT_NO": ["NA", "LOT-1", "LOT-2", "LOT-3", "LOT-4", "LOT-5"],
            "Line": ["LINE-A", "LINE-B", "LINE-C", "LINE-D", "LINE-E", "AUTOMATION LINE", "SUB ASSEMBLY"],
            "VI-1": ["WEAK WELD", "DUST WELD", "IMPROPER WELD", "AIR BUBBLES", "DAMAGE", "NARROW CHANNEL", "ALIGNMENT ISSUE", "QC TORQUE TEST", "CHILD PARTS WELDED", "HAIR WELD", "DUMP REJECTIONS", "OIL", "BULGING", "NA"],
            "VI-2": ["WEAK WELD", "DUST WELD", "IMPROPER WELD", "AIR BUBBLES", "DAMAGE", "ALIGNMENT ISSUE", "WHITE LINE", "NARROW CHANNEL"],
            "VI-3": ["PEAL OFF", "TEAR OFF", "DAMAGE", "DUST WELD", "IMPROPER WELD", "OVERMELT", "NARROW CHANNEL"],
            "VACCUM REJECTIONS": ["EN 6 LEAK", "EN 4 LEAK", "SN LOW", "SN HIGH", "EN LOW", "EN HIGH", "QR REJECTIONS", "CLOCKED ERROR", "DAMAGE","NA"],
            "VI-4": ["IMPROPER WELDING", "WEAK WELDING", "DUST WELD", "ALIGNMENT ISSUE", "QR REJECTIONS", "DAMAGE", "OVERMELT", "NARROW CHANNEL", "MATRIC REJECTIONS", "SEALING REJECTIONS", "AIR BUBBLES", "WELDING REJECTIONS", "NA"],
            "CHILD PARTS": ["MATRIX", "LEFT VALVE CAPS", "RIGHT VALVE CAPS", "ASSEMBLED SMILEY", "OVERMOULD SMILEY", "GROMMET", "NA", "SMILEY", "FILTER RODS", "SAMPLE FILTER", "SMALL DUMP", "QR CODE LABELS", "VALVE BODY"],
            "Equipment_LINE_A": ["EC/EQID/III-00631", "EC/EQID/III-00163"],
            "Equipment_LINE_B": ["EC/EQID/III-00572", "EC/EQID/III-00133"],
            "Equipment_LINE_C": ["EC/EQID/III-00069", "EC/EQID/III-00101"],
            "Equipment_LINE_D": ["EC/EQID/III-00003", "EC/EQID/III-00633"],
            "Equipment_LINE_E": ["EC/EQID/III-00036", "EC/EQID/III-00632"],
            "Equipment_AUTOMATION_LINE": ["EC/EQID/III-00659"],
            "CartridgePart": ["NA", "BUFFER CHANNEL SIDE","ELUTE SIDE", "MATRIX SIDE", "SAMPLE FILETER SIDE", "DUMP SIDE", "FILTER RODS SIDE", "SAMPLE FILTER BOTTOM","VALVE CAP DAMAGE", "IN CHANNEL", "QR CODE"],
            "VerifiedByName": ["L R NAIDU", "KAUSHIK", "SAI KUMAR", "SRINU", "ROHINII", "KISHORE", "RAJU", "RAVI TEJA","AZAD"]
        }

        self.build_header_section()
        self.build_item_section()
        self.build_table_section()
        
        self.set_default_date_and_shift()
        self.start_timer()

    def show_modern_alert(self, title, message, is_error=True):
        popup = ctk.CTkToplevel(self.app)
        popup.title(title)
        popup.geometry("400x220")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)
        
        popup.update_idletasks()
        try:
            x = self.app.winfo_x() + (self.app.winfo_width() // 2) - 200
            y = self.app.winfo_y() + (self.app.winfo_height() // 2) - 110
            popup.geometry(f"+{x}+{y}")
        except:
            pass
            
        popup.configure(fg_color=CARD_BG)
        
        icon = "⚠️" if is_error else "✅"
        color = "#d92d44" if is_error else "#2d8a4e"
        
        icon_lbl = ctk.CTkLabel(popup, text=icon, font=ctk.CTkFont(size=40))
        icon_lbl.pack(pady=(20, 5))
        
        title_lbl = ctk.CTkLabel(popup, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
        title_lbl.pack(pady=0)
        
        msg_lbl = ctk.CTkLabel(popup, text=message, font=ctk.CTkFont(size=13), text_color=TEXT_PRIMARY, wraplength=350, justify="center")
        msg_lbl.pack(pady=(10, 15), padx=20)
        
        btn = ctk.CTkButton(popup, text="OK", font=ctk.CTkFont(weight="bold"), fg_color=color, hover_color=color, command=popup.destroy)
        btn.pack(pady=(0, 20))

    def start_timer(self):
        self.set_default_date_and_shift()
        self.after(60000, self.start_timer)

    def set_default_date_and_shift(self):
        now = datetime.now()
        hours = now.hour
        shift = ""
        logical_date = now

        if 6 <= hours < 14:
            shift = "A-SHIFT"
        elif 14 <= hours < 22:
            shift = "B-SHIFT"
        else:
            shift = "C-SHIFT"
            if 0 <= hours < 6:
                logical_date = logical_date - timedelta(days=1)

        date_str = logical_date.strftime("%Y-%m-%d")
        
        if hasattr(self, 'date_entry'):
            self.date_entry.configure(state="normal")
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, date_str)
        if hasattr(self, 'shift_combo'):
            self.shift_combo.set(shift)

    def build_field(self, parent, col_idx, label_text, is_combo=False, values=None, placeholder="", command=None):
        parent.grid_columnconfigure(col_idx, weight=1)
        
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col_idx, sticky="ew", padx=(0, 15), pady=(0, 10))
        
        lbl = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_SECONDARY)
        lbl.pack(anchor="w", pady=(0, 4))
        
        if is_combo:
            wrapper = ctk.CTkFrame(frame, height=36, corner_radius=6, border_width=1, border_color="#c4d1eb", fg_color="#f9fbfd")
            wrapper.pack_propagate(False)
            widget = ctk.CTkOptionMenu(wrapper, values=values or ["NA"], command=command, **COMBO_STYLE)
            widget.pack(fill="both", expand=True, padx=2, pady=2)
            wrapper.pack(fill="x", expand=True)
        else:
            widget = ctk.CTkEntry(frame, placeholder_text=placeholder, **INPUT_STYLE)
            widget.pack(fill="x", expand=True)
            
        return widget

    def build_header_section(self):
        frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(25, 10))
        
        title = ctk.CTkLabel(frame, text="📝 Batch Details", font=ctk.CTkFont(size=18, weight="bold"), text_color=PRIMARY_BLUE)
        title.pack(anchor="w", padx=25, pady=(20, 15))
        
        fields_frame = ctk.CTkFrame(frame, fg_color="transparent")
        fields_frame.pack(fill="x", expand=True, padx=25, pady=(0, 20))

        self.date_entry = self.build_field(fields_frame, 0, "Date")
        self.shift_combo = self.build_field(fields_frame, 1, "Shift", True, self.lookups["Shift"])
        self.line_combo = self.build_field(fields_frame, 2, "Line", True, self.lookups["Line"], command=self.on_line_change)
        self.line_combo.set("Select")
        self.batch_entry = self.build_field(fields_frame, 3, "Batch No", False, placeholder="e.g. B1024")
        self.lot_combo = self.build_field(fields_frame, 4, "Lot No", True, self.lookups["LOT_NO"])
        self.lot_combo.set("NA")
        self.verified_combo = self.build_field(fields_frame, 5, "Verified By", True, self.lookups["VerifiedByName"])
        self.verified_combo.set("Select")

    def build_item_section(self):
        frame = ctk.CTkFrame(self, fg_color="#f1f6fc", corner_radius=12, border_color="#dbe2ea", border_width=1)
        frame.grid(row=1, column=0, sticky="ew", padx=25, pady=10)
        
        title = ctk.CTkLabel(frame, text="🚨 Add Rejection Details", font=ctk.CTkFont(size=18, weight="bold"), text_color="#18324a")
        title.pack(anchor="w", padx=25, pady=(20, 15))
        
        fields_frame = ctk.CTkFrame(frame, fg_color="transparent")
        fields_frame.pack(fill="x", expand=True, padx=25, pady=(0, 20))

        stages = ["VI-1", "VI-2", "VI-3", "VACCUM REJECTIONS", "VI-4", "CHILD PARTS"]
        self.stage_combo = self.build_field(fields_frame, 0, "Rejection Stage", True, stages, command=self.on_stage_change)
        self.stage_combo.set("Select")

        self.equip_combo = self.build_field(fields_frame, 1, "Equipment ID", True, ["NA"])
        self.equip_combo.configure(state="disabled")
        self.equip_combo.set("NA")

        self.type_combo = self.build_field(fields_frame, 2, "Type of Rejection", True, ["NA"])
        self.type_combo.set("NA")

        self.part_combo = self.build_field(fields_frame, 3, "Cartridge Part", True, self.lookups["CartridgePart"])
        self.part_combo.set("Select")

        self.qty_entry = self.build_field(fields_frame, 4, "Qty", False, placeholder="0")

        btn_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=5, sticky="ew", padx=(0, 0), pady=(0, 10))
        fields_frame.grid_columnconfigure(5, weight=1)
        
        lbl = ctk.CTkLabel(btn_frame, text="", font=ctk.CTkFont(size=13))
        lbl.pack(pady=(0, 4))
        
        btn = ctk.CTkButton(btn_frame, text="➕ Add Item", height=36, font=ctk.CTkFont(size=14, weight="bold"), 
                            corner_radius=6, fg_color=PRIMARY_BLUE, hover_color=HOVER_BLUE, command=self.add_item)
        btn.pack(fill="x", expand=True)

    def build_table_section(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=25, pady=(10, 20))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.table_scroll = ctk.CTkScrollableFrame(container, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.table_scroll.grid(row=0, column=0, sticky="nsew")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        
        self.summary_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        self.summary_frame.pack(side="left", fill="x", expand=True)

        self.submit_btn = ctk.CTkButton(btn_frame, text="🚀 Submit All Data", font=ctk.CTkFont(size=14, weight="bold"), 
                                        height=42, width=170, corner_radius=8, fg_color=PRIMARY_BLUE, hover_color=HOVER_BLUE, command=self.submit_data)
        self.submit_btn.pack(side="right")
        
        self.render_table()

    def on_line_change(self, value):
        if self.stage_combo.get() == "VI-1":
            line = self.line_combo.get()
            key = "Equipment_" + line.replace("-", "_").replace(" ", "_")
            options = self.lookups.get(key, ["NA"])
            self.equip_combo.configure(values=options)
            self.equip_combo.configure(state="normal")
            if options: self.equip_combo.set(options[0])

    def on_stage_change(self, value):
        stage = self.stage_combo.get()
        
        options = self.lookups.get(stage, ["NA"])
        self.type_combo.configure(values=options)
        if options: self.type_combo.set(options[0])
        else: self.type_combo.set("NA")
        
        if stage == "VI-1":
            self.equip_combo.configure(state="normal")
            line = self.line_combo.get()
            if line and line != "Select":
                key = "Equipment_" + line.replace("-", "_").replace(" ", "_")
                e_opts = self.lookups.get(key, ["NA"])
                self.equip_combo.configure(values=e_opts)
                if e_opts: self.equip_combo.set(e_opts[0])
            else:
                self.equip_combo.configure(values=["NA"])
                self.equip_combo.set("NA")
        else:
            self.equip_combo.configure(state="disabled", values=["NA"])
            self.equip_combo.set("NA")

    def add_item(self):
        stage = self.stage_combo.get()
        equipment = self.equip_combo.get()
        rtype = self.type_combo.get()
        part = self.part_combo.get()
        qty = self.qty_entry.get().strip()

        if not stage or stage == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Rejection Stage.")
            
        if stage == "VI-1" and (not equipment or equipment == "Select"):
            return self.show_modern_alert("Validation Error", "Please select an Equipment ID.")
            
        if not rtype or rtype == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Type of Rejection.")
            
        if not part or part == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Cartridge Part.")
            
        if not qty:
            return self.show_modern_alert("Validation Error", "Please enter the Quantity.")

        try:
            qty_val = int(qty)
            if qty_val <= 0: raise ValueError
        except:
            return self.show_modern_alert("Validation Error", "Quantity must be a valid number greater than 0.")

        self.rejection_items.append({
            "stage": stage,
            "equipment": equipment if equipment else "NA",
            "type": rtype if rtype else "NA",
            "part": part if part != "Select" else "NA",
            "qty": qty_val
        })

        self.render_table()

        self.qty_entry.delete(0, "end")
        self.part_combo.set("Select")

    def remove_item(self, idx):
        if 0 <= idx < len(self.rejection_items):
            self.rejection_items.pop(idx)
            self.render_table()

    def render_table(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        if not self.rejection_items:
            empty_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=60)
            
            icon_lbl = ctk.CTkLabel(empty_frame, text="📭", font=ctk.CTkFont(size=60))
            icon_lbl.pack(pady=(0, 10))
            
            text_lbl = ctk.CTkLabel(empty_frame, text="No Rejections Added Yet", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_PRIMARY)
            text_lbl.pack(pady=(0, 5))
            
            sub_lbl = ctk.CTkLabel(empty_frame, text="Fill out the details above and click '➕ Add Item' to start building your list.", font=ctk.CTkFont(size=14), text_color=TEXT_SECONDARY)
            sub_lbl.pack()
            return

        grid_frame = ctk.CTkFrame(self.table_scroll, fg_color=BORDER_COLOR, corner_radius=0)
        grid_frame.pack(fill="x", expand=True, padx=2, pady=2)

        headers = ["Stage", "Equipment ID", "Type", "Cartridge Part", "Qty", "Action"]
        col_weights = [1, 1, 2, 2, 0, 0]
        
        for col, w in enumerate(col_weights):
            grid_frame.grid_columnconfigure(col, weight=w)

        for col, h in enumerate(headers):
            cell = ctk.CTkFrame(grid_frame, fg_color="#eef5ff", corner_radius=0)
            cell.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            lbl = ctk.CTkLabel(cell, text=h, font=ctk.CTkFont(size=13, weight="bold"), text_color=PRIMARY_BLUE)
            lbl.pack(padx=10, pady=8, anchor="w")

        stage_totals = {}
        for row, item in enumerate(self.rejection_items, start=1):
            stage = item["stage"]
            qty = item["qty"]
            stage_totals[stage] = stage_totals.get(stage, 0) + qty
            
            row_vals = [stage, item["equipment"], item["type"], item["part"], str(qty)]
            
            for col, val in enumerate(row_vals):
                cell = ctk.CTkFrame(grid_frame, fg_color=CARD_BG, corner_radius=0)
                cell.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                font = ctk.CTkFont(size=14, weight="bold") if col == 4 else ctk.CTkFont(size=13)
                lbl = ctk.CTkLabel(cell, text=val, font=font, text_color=TEXT_PRIMARY)
                lbl.pack(padx=10, pady=6, anchor="w")
                
            act_cell = ctk.CTkFrame(grid_frame, fg_color=CARD_BG, corner_radius=0)
            act_cell.grid(row=row, column=5, sticky="nsew", padx=1, pady=1)
            del_btn = ctk.CTkButton(act_cell, text="Remove", width=70, height=26, corner_radius=4, font=ctk.CTkFont(size=12, weight="bold"), 
                                    fg_color="#d92d44", hover_color="#b1142d", command=lambda idx=row-1: self.remove_item(idx))
            del_btn.pack(padx=10, pady=4)

        summ_lbl = ctk.CTkLabel(self.summary_frame, text="Total Quantity:", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY)
        summ_lbl.pack(side="left", padx=(0, 10))
        
        for stg, tot in stage_totals.items():
            badge = ctk.CTkFrame(self.summary_frame, fg_color="#eef5ff", corner_radius=6, border_color="#c4d1eb", border_width=1)
            badge.pack(side="left", padx=5)
            lbl = ctk.CTkLabel(badge, text=f"{stg}: {tot}", font=ctk.CTkFont(size=13, weight="bold"), text_color=PRIMARY_BLUE)
            lbl.pack(padx=10, pady=4)

    def submit_data(self):
        date_val = self.date_entry.get().strip()
        shift = self.shift_combo.get()
        batch = self.batch_entry.get().strip()
        lot = self.lot_combo.get()
        line = self.line_combo.get()
        verified = self.verified_combo.get()

        if not date_val:
            return self.show_modern_alert("Validation Error", "Please enter a valid Date in the Header Info.")
        if not shift or shift == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Shift.")
        if not line or line == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Line.")
        if not batch:
            return self.show_modern_alert("Validation Error", "Please enter the Batch No.")
        if not lot:
            return self.show_modern_alert("Validation Error", "Please select the Lot No.")
        if not verified or verified == "Select":
            return self.show_modern_alert("Validation Error", "Please select a Verified By person.")

        if not self.rejection_items:
            return self.show_modern_alert("Validation Error", "Please add at least one rejection item to the list.")

        try:
            d_obj = datetime.strptime(date_val, "%Y-%m-%d")
            formatted_date = d_obj.strftime("%d/%m/%Y")
        except:
            formatted_date = date_val

        self.submit_btn.configure(state="disabled", text="Submitting...")
        self.app.update()

        success_count = 0
        fail_count = 0

        for item in self.rejection_items:
            payload = {
                "Date": formatted_date,
                "Shift": shift,
                "BatchNo": batch,
                "LotNo": lot,
                "Line": line,
                "RejectionStage": item["stage"],
                "EquipmentID": item["equipment"],
                "TypeOfRejections": item["type"],
                "CartridgePart": item["part"],
                "Qty": item["qty"],
                "VerifiedBy": verified
            }

            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(self.WEBHOOK_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status in [200, 202]:
                        success_count += 1
                    else:
                        fail_count += 1
            except Exception as e:
                print("Submission Error:", e)
                fail_count += 1

        self.submit_btn.configure(state="normal", text="🚀 Submit All Data")

        if fail_count == 0:
            self.show_modern_alert("Success", f"Successfully submitted {success_count} record(s) to SharePoint!", is_error=False)
            self.rejection_items = []
            self.render_table()
            self.batch_entry.delete(0, "end")
            self.line_combo.set("Select")
        else:
            self.show_modern_alert("Partial Failure", f"Submitted {success_count} record(s). Failed {fail_count}. Check your internet connection.", is_error=True)
