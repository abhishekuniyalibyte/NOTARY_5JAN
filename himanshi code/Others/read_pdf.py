import pymupdf

doc=pymupdf.open("Ley_Orgánica_Notarial_y_Reglamento_Notarial.pdf")
lower_page=80
higher_page=84
for page_number in range(lower_page, higher_page + 1):
    page=doc.load_page(page_number)
    text=page.get_text("text")
    with open(f"page_{page_number}.txt", "w", encoding="utf-8") as text_file:
        text_file.write(text)
