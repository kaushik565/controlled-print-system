import fitz
import os

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")

original = fitz.open(pdf_path)
page_idx = 0

new_doc = fitz.open()
new_doc.insert_pdf(original, from_page=page_idx, to_page=page_idx)
page = new_doc[0]

# Try setting rotation to 0 first!
rot = page.rotation
page.set_rotation(0)

# Now the page is in its native (unrotated) state.
# We want to place the watermark so that when it is rotated back by `rot`, it appears at the bottom right.
# Let's define the 4 possible corners depending on `rot`.
# In the native state, the width and height are:
w = page.rect.width
h = page.rect.height

# We will just insert a shape or text to test where it ends up!
text = "TEST WATERMARK"
text_len = fitz.get_text_length(text, fontname="helv", fontsize=18)

# Calculate positions based on rotation
if rot == 0:
    x = w - 20 - text_len
    y = h - 20
    text_rot = 0
elif rot == 90:
    # After 90 deg clockwise, native Top-Right becomes visible Bottom-Right
    x = w - 20
    y = 20 + text_len
    text_rot = 270 # or -90
elif rot == 180:
    # After 180 deg, native Top-Left becomes visible Bottom-Right
    x = 20 + text_len
    y = 20
    text_rot = 180
elif rot == 270:
    # After 270 deg clockwise, native Bottom-Left becomes visible Bottom-Right
    x = 20
    y = h - 20 - text_len
    text_rot = 90

p = fitz.Point(x, y)
page.insert_text(p, text, fontname="helv", fontsize=18, color=(1, 0, 0), morph=(p, fitz.Matrix(text_rot)))

# Restore rotation
page.set_rotation(rot)

pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
pix.save("test_rotation_logic.png")

new_doc.save("test_rotation_logic.pdf")
new_doc.close()
original.close()

print("Generated test_rotation_logic.png")
