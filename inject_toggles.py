with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # 1. End of build_preview_pane
    if 'up_btn.pack(pady=(0, 10))' in line:
        pass # Not end, wait
    if 'right_col.grid(row=0, column=1, sticky="e", padx=(10, 0))' in line:
        pass
        
    # Wait, let's just insert toggle_right_pane calls specifically
    if 'def build_preview_pane(self, parent):' in lines[max(0, i-60):i] and 'right_col.grid(row=0, column=1' in line:
        pass

    if line.strip() == 'self.current_preview_log = None' and 'def clear_queue' in ''.join(lines[max(0, i-15):i]):
        new_lines.append('        self.toggle_right_pane()\n')
        
    if line.strip() == 'self.current_preview_log = None' and 'def preview_document' in ''.join(lines[max(0, i-10):i]):
        new_lines.append('            self.toggle_right_pane()\n')
        
    if line.strip() == 'self.preview_image_label.configure(image=ctk_img, text="")':
        new_lines.append('            self.toggle_right_pane()\n')
        
    if line.strip() == 'self.opacity_slider.pack(fill="x", pady=(0, 0))':
        # Let's insert toggle_right_pane right after build_preview_pane completes
        pass

# Append toggle to end of build_preview_pane by finding 'up_btn = ctk.CTkButton' block end.
# Actually we can just run self.toggle_right_pane() in build_ui after build_preview_pane is done!
# Or right after self.switch_frame in __init__
# Let's just insert it in __init__ after build_ui

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
# Add to __init__
with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('self.switch_frame("🖨️ Batch Print")', 'self.switch_frame("🖨️ Batch Print")\n        self.toggle_right_pane()')
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Toggle calls injected.")
