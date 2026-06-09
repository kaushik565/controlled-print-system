import os

methods_code = """
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
            
        self.favorites_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        self.favorites_frame.grid_rowconfigure((0, 1), weight=1, uniform="row")
        
        for i in range(6):
            row = i // 3
            col = i % 3
            fav_data = getattr(self, 'favorites', [None]*6)[i]
            
            card = ctk.CTkFrame(self.favorites_frame, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
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
                
                doc_lbl = ctk.CTkLabel(inner, text=f"{fav_data.get('format_id', '')} (Rev {fav_data.get('revision', '')})", font=ctk.CTkFont(size=10), text_color=TEXT_SECONDARY)
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
        from datetime import datetime
        fav_data = self.favorites[index]
        if not fav_data: return
        
        dialog = ctk.CTkInputDialog(text=f"Enter number of copies for '{fav_data['custom_name']}':", title="Print Favorite")
        copies_str = dialog.get_input()
        if not copies_str or not copies_str.isdigit() or int(copies_str) < 1: return
            
        copies = int(copies_str)
        today = datetime.now().strftime("%d/%m/%Y")
        wm_text = f"AUTHORISED COPY - {today}"
        
        old_text = self.watermark_text.get()
        self.watermark_text.set(wm_text)
        
        log = {
            "batch_no": "FAV",
            "format_id": fav_data['format_id'],
            "revision": fav_data['revision'],
            "summary": "Favorite Print",
            "parsed_copies": [{"page": None, "copies": copies}],
            "status": "PENDING"
        }
        
        self.generate_watermarked_doc(log)
        self.watermark_text.set(old_text)

"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('    def build_status_bar(self):'):
        new_lines.append(methods_code)
    new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Methods successfully injected.")
