import fitz
import os

pdf_path = os.path.join("repository", "FM-QP-III-061-02.pdf")
original = fitz.open(pdf_path)
page = original[0]

text = "AUTHORISED COPY\nMVANC00108"
text_length = fitz.get_text_length("AUTHORISED COPY", fontname="helv", fontsize=18)

# Visible destination point (bottom right)
p_vis = fitz.Point(page.rect.x1 - text_length - 20, page.rect.y1 - 60)

# Map to unrotated
p_unrot = p_vis * page.derotation_matrix

# Rotate text opposite to page rotation so it appears upright!
# If page is 270, we want text to be -270 (which is 90)
rot_matrix = fitz.Matrix(-page.rotation)

# Insert text
page.insert_text(p_unrot, text, fontname="helv", fontsize=18, color=(0.5, 0.5, 0.5), fill_opacity=0.4, morph=(p_unrot, rot_matrix))

# Save and generate PNG to verify
original.save("test_morph.pdf")
page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0)).save("test_morph.png")
original.close()

print("Generated test_morph.pdf and test_morph.png")
