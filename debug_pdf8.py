import fitz
import os

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")

original = fitz.open(pdf_path)
page_idx = 0

new_doc = fitz.open()
new_doc.insert_pdf(original, from_page=page_idx, to_page=page_idx)
page = new_doc[0]

date_str = "23/05/2026"
wm_text = "AUTHORISED COPY"
batch_no = "MVANC00108"
lines = [f"{wm_text} {date_str}", batch_no]

y_vis = page.rect.y1 - 20

for line in reversed(lines):
    line_len = fitz.get_text_length(line, fontname="helv", fontsize=18)
    p_vis = fitz.Point(page.rect.x1 - 20 - line_len, y_vis)
    p_unrot = p_vis * page.derotation_matrix
    text_rot = fitz.Matrix(-page.rotation)
    page.insert_text(p_unrot, line, fontname="helv", fontsize=18, color=(0.5, 0.5, 0.5), fill_opacity=0.4, morph=(p_unrot, text_rot))
    y_vis -= 22

pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
pix.save("test_perfect.png")

new_doc.save("test_perfect.pdf")
new_doc.close()
original.close()

print("Generated test_perfect.png and test_perfect.pdf")
