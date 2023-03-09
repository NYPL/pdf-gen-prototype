import pdf_gen.djvu_generator as djvu

def test_generate_pdf_page():
    djvu.generate_pdf_page("tests/data/djvu.xml", "djvu_img.jp2", "test_out.pdf")

