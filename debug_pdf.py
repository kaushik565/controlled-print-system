import sqlite3
import fitz
import os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

DB_NAME = "database.db"
REPOSITORY = "repository"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT file_path FROM documents WHERE status='ACTIVE'")
results = cursor.fetchall()
conn.close()

if not results:
    print("No documents found!")
    exit()

pdf_path = None
for res in results:
    filename = os.path.basename(res[0])
    path = os.path.join(REPOSITORY, filename)
    if os.path.exists(path):
        pdf_path = path
        break

if not pdf_path:
    print("No physical files found in repository!")
    exit()

print(f"Testing with: {pdf_path}")

doc = fitz.open(pdf_path)
page = doc[0]

print(f"Page 0 rect: {page.rect}")
print(f"Page 0 mediabox: {page.mediabox}")
print(f"Page 0 cropbox: {page.cropbox}")
print(f"Page 0 rotation: {page.rotation}")

width = page.rect.width
height = page.rect.height

print(f"Creating watermark with width={width}, height={height}")

output_pdf = "debug_wm.pdf"
c = canvas.Canvas(output_pdf, pagesize=(width, height))
c.setFillColor(Color(1, 0, 0, alpha=1.0)) # Solid red
c.setFont("Helvetica", 18)

lines = ["AUTHORISED COPY 23/05/2026", "MVANC00108"]
x = width - 10
y = 40

for line in lines:
    c.drawRightString(x, y, line)
    y -= 20
c.save()

watermark = fitz.open(output_pdf)

new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=0, to_page=0)
for p in new_doc:
    p.show_pdf_page(p.rect, watermark, 0)

new_doc.save("debug_final.pdf")
new_doc.close()
doc.close()
watermark.close()

print("Generated debug_final.pdf")
