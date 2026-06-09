import fitz

doc = fitz.open()
page = doc.new_page()

try:
    page.insert_font(fontname="arial", fontfile="C:/Windows/Fonts/arial.ttf")
    # try getting text length
    l1 = fitz.get_text_length("AUTHORISED COPY", fontname="helv", fontsize=18)
    # to get arial length we can either use the font name if it's loaded in fitz?
    # actually get_text_length takes fontname, but fitz might not know "arial" natively
    font = fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf")
    l2 = font.text_length("AUTHORISED COPY", fontsize=18)
    
    print(f"Helv length: {l1}")
    print(f"Arial length: {l2}")
except Exception as e:
    print(f"Failed: {e}")

doc.close()
