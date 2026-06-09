import fitz
import os

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")
original = fitz.open(pdf_path)
page_idx = 0
orig_page = original[page_idx]
width = orig_page.rect.width
height = orig_page.rect.height
rot = orig_page.rotation

print(f"Original: {width}x{height}, Rotation: {rot}")

new_doc = fitz.open()
new_page = new_doc.new_page(width=width, height=height)

# Try passing rotation!
new_page.show_pdf_page(new_page.rect, original, page_idx, rotation=rot)

new_doc.save("test_rotation_fix.pdf")
new_doc.close()
original.close()

print("Generated test_rotation_fix.pdf")
