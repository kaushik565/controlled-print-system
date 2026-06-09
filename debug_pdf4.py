import fitz
import os
from datetime import datetime

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")
original = fitz.open(pdf_path)
page = original[0]

# Visible rect
rect = page.rect
print(f"Visible Rect: {rect}")

text = f"AUTHORISED COPY {datetime.now().strftime('%d/%m/%Y')}\nMVANC00108"

# Calculate a bounding box for the text at the bottom right
# Let's say text box is 300 wide, 60 tall
w = 300
h = 60
x0 = rect.width - w - 20
y0 = rect.height - h - 40
x1 = rect.width - 20
y1 = rect.height - 40

annot_rect = fitz.Rect(x0, y0, x1, y1)

# Add FreeText
annot = page.add_freetext_annot(annot_rect, text, fontsize=18, fontname="helv", text_color=(0.5, 0.5, 0.5))
annot.set_opacity(0.4)
# Align right? FreeText align: 0=left, 1=center, 2=right
# In fitz, add_freetext_annot has align param
annot.set_info(title="Watermark")
annot.update()

original.save("test_annot.pdf")
original.close()

print("Generated test_annot.pdf")
