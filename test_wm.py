import fitz
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
import os

width, height = 595.27, 841.89

# 1. Create original mock PDF (blank)
doc = fitz.open()
page = doc.new_page(width=width, height=height)
page.draw_rect(page.rect, color=(1, 1, 1), fill=(1, 1, 1))
doc.save("test_orig.pdf")
doc.close()

# 2. Create watermark
output_pdf = "test_wm.pdf"
c = canvas.Canvas(output_pdf, pagesize=(width, height))
c.saveState()
c.setFillColor(Color(1, 0, 0, alpha=1.0)) # RED, full opacity for testing
c.setFont("Helvetica", 18)

lines = [
    "AUTHORISED COPY 23/05/2026",
    "MVANC00018"
]

x = width - 10
y = 40

for line in lines:
    c.drawRightString(x, y, line)
    y -= 20

c.restoreState()
c.save()

# 3. Combine
original = fitz.open("test_orig.pdf")
watermark = fitz.open("test_wm.pdf")

for page in original:
    page.show_pdf_page(page.rect, watermark, 0)

original.save("test_final.pdf")
original.close()
watermark.close()

print("Test complete. Check test_final.pdf")
