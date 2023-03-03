from ocrmypdf.hocrtransform import HocrTransform


def generate_pdf_page(hocr_filename: str, image_filename: str, out_filename: str):
    hocr = HocrTransform(hocr_filename=hocr_filename, dpi=720)
    hocr.to_pdf(out_filename=out_filename, image_filename=image_filename)
