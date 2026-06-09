import fitz
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")
original = fitz.open(pdf_path)
page_idx = 0
target_page = original[page_idx]
width = target_page.rect.width
height = target_page.rect.height

# Create watermark matching visible dimensions
watermark_pdf = "test_wm3.pdf"
c = canvas.Canvas(watermark_pdf, pagesize=(width, height))
c.setFillColor(Color(1, 0, 0, alpha=1.0)) # Solid red for visibility
c.setFont("Helvetica", 18)
c.drawRightString(width - 20, 60, "AUTHORISED COPY 23/05/2026")
c.drawRightString(width - 20, 40, "MVANC00108")
c.save()

watermark = fitz.open(watermark_pdf)

# Flatten rotation by creating a new page
new_doc = fitz.open()
new_page = new_doc.new_page(width=width, height=height)

# Draw original page (this bakes the rotation)
new_page.show_pdf_page(new_page.rect, original, page_idx)

# Draw watermark
new_page.show_pdf_page(new_page.rect, watermark, 0)

new_doc.save("test_final3.pdf")
new_doc.close()
original.close()
watermark.close()

print("Generated test_final3.pdf")
