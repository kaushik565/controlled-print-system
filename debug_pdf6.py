import fitz
import os
from datetime import datetime

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")

original = fitz.open(pdf_path)
page_idx = 0

new_doc = fitz.open()
new_doc.insert_pdf(original, from_page=page_idx, to_page=page_idx)
page = new_doc[0]

date_str = "23/05/2026"
wm_text = "AUTHORISED COPY"
batch_no = "MVANC00108"
text = f"{wm_text} {date_str}\n{batch_no}"

w = 400
h = 80
rect = page.rect
annot_rect = fitz.Rect(rect.x1 - w - 20, rect.y1 - h - 20, rect.x1 - 20, rect.y1 - 20)
annot = page.add_freetext_annot(annot_rect, text, fontsize=18, fontname="helv", text_color=(0.5, 0.5, 0.5), align=2)
annot.set_opacity(0.4)
annot.update()

pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
pix.save("test_app_output.png")

new_doc.save("test_app_output.pdf")
new_doc.close()
original.close()

print("Generated test_app_output.png")
