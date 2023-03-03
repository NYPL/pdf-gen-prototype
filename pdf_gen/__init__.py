import tempfile

import pdf_gen.mets_parser
import pdf_gen.page_generator
from PyPDF2 import PdfMerger


def generate(dir_file: str, ocr_dir: str, out_filename: str):
    # In order sequence of generated pages
    merger = PdfMerger()
    with tempfile.TemporaryDirectory() as tmpdirname:
        for page in pdf_gen.mets_parser.iter_pages(dir_file):
            local_name = page.image_file.fid + ".pdf"
            print(f"Preparing to generate pdf {local_name}")
            full_name = tmpdirname + "/" + local_name
            if not page.ocr_file.location:
                print("No text, skipping for now")
                continue
            print(f"Resetting hocr file doc type")
            pdf_gen.mets_parser.reset_doctype(ocr_dir + page.ocr_file.location)
            print("Generating pdf")
            pdf_gen.page_generator.generate_pdf_page(
                hocr_filename=(ocr_dir + page.ocr_file.location),
                image_filename=(ocr_dir + page.image_file.location),
                out_filename=full_name,
            )

            merger.append(full_name)

        print("Merging temp pdfs")
        with open(out_filename, "wb") as merged_pdf:
            merger.write(merged_pdf)


if __name__ == "__main__":
    generate(
        dir_file="/Users/sarangjoshi/code/pdf-gen/data/c3263821/UCAL_C3263821.xml",
        ocr_dir="/Users/sarangjoshi/code/pdf-gen/data/c3263821/",
        out_filename="/Users/sarangjoshi/code/pdf-gen/sample.pdf",
    )
