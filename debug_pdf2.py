import sqlite3
import fitz
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

DB_NAME = "database.db"
REPOSITORY = "repository"

# Find the specific file
pdf_path = os.path.join(REPOSITORY, "FM-QP-III-061-02.pdf")
if not os.path.exists(pdf_path):
    print("File not found:", pdf_path)
    exit()

print("Testing with:", pdf_path)

# Extract first page
original = fitz.open(pdf_path)
page_idx = 0
target_page = original[page_idx]
width = target_page.rect.width
height = target_page.rect.height

print(f"Original Rect: {target_page.rect}")
print(f"Original CropBox: {target_page.cropbox}")
print(f"Original Rotation: {target_page.rotation}")
print(f"Width: {width}, Height: {height}")

# Create watermark
watermark_pdf = "test_wm2.pdf"
c = canvas.Canvas(watermark_pdf, pagesize=(width, height))
c.saveState()

# Let's try SOLID BLACK to ensure it's not an opacity/color issue
c.setFillColor(Color(0, 0, 0, alpha=1.0))
c.setFont("Helvetica", 18)

lines = [
    "AUTHORISED COPY 23/05/2026",
    "MVANC00108"
]

x = width - 20
y = 60

print(f"Drawing text at x={x}, y={y}")

for line in lines:
    c.drawRightString(x, y, line)
    y -= 20

c.restoreState()
c.save()

# Combine
watermark = fitz.open(watermark_pdf)
new_doc = fitz.open()
new_doc.insert_pdf(original, from_page=page_idx, to_page=page_idx)

page = new_doc[0]
page.show_pdf_page(page.rect, watermark, 0)
new_doc.save("test_final2.pdf")

# Generate Image to see if it's visible in rendering
pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
pix.save("test_final2.png")

print("Generated test_final2.pdf and test_final2.png")
new_doc.close()
original.close()
watermark.close()
