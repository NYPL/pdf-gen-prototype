import argparse
import os.path
import tempfile

import pdf_gen.djvu_generator
import pdf_gen.mets_parser
import pdf_gen.page_generator
from PyPDF2 import PdfMerger

_DEFAULT_MANIFEST = "data/c3263821/UCAL_C3263821.xml"
_DEFAULT_OCR_DIR = "data/c3263821/"
_DEFAULT_OUTFILE ="sample.pdf"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', dest='manifest', action='store', default=_DEFAULT_MANIFEST)
    parser.add_argument('--ocr-dir', dest='ocr_dir', action='store', default=_DEFAULT_OCR_DIR)
    parser.add_argument('--outfile', dest='outfile', action='store', default=_DEFAULT_OUTFILE)
    args = parser.parse_args()
    generate(
        dir_file=args.manifest,
        ocr_dir=args.ocr_dir,
        out_filename=args.outfile,
    )


def generate(dir_file: str, ocr_dir: str, out_filename: str):
    # In order sequence of generated pages
    merger = PdfMerger()
    total_filesize = 0
    with tempfile.TemporaryDirectory() as tmpdirname:
        for page in pdf_gen.mets_parser.iter_pages(dir_file):
            print(page)
            local_name = page.image_file.fid + ".pdf"
            print(f"Preparing to generate pdf {local_name}")
            full_name = tmpdirname + "/" + local_name
            if not page.ocr_file.location:
                print("No text, skipping for now")
                continue
            if pdf_gen.mets_parser.is_djvu_xml(ocr_dir + page.ocr_file.location):
                pdf_gen.djvu_generator.generate_pdf_page(
                    djvu_filename=(ocr_dir + page.ocr_file.location),
                    image_filename=(ocr_dir + page.image_file.location),
                    out_filename=full_name,
                )
            else:
                modded_ocr_location = f"{tmpdirname}/{page.ocr_file.location}"
                print(f"Resetting hocr file doc type")
                pdf_gen.mets_parser.reset_hocr_doctype(
                    ocr_file_location=(ocr_dir + page.ocr_file.location),
                    outfile_location=modded_ocr_location,
                )
                print("Generating pdf")
                pdf_gen.page_generator.generate_pdf_page(
                    hocr_filename=modded_ocr_location,
                    image_filename=(ocr_dir + page.image_file.location),
                    out_filename=full_name,
                )
                print(f"Output file size {os.path.getsize(full_name)}")
                total_filesize += os.path.getsize(full_name)

            merger.append(full_name)

        print(f"Total size: {total_filesize}")

        print("Merging temp pdfs")
        with open(out_filename, "wb") as merged_pdf:
            merger.write(merged_pdf)


if __name__ == "__main__":
    main()
