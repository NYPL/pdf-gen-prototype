import argparse
import os.path

import pypdf
from pypdf.generic import AnnotationBuilder

import pdf_gen.djvu_generator
import pdf_gen.mets_parser
import pdf_gen.ocr_dir
import pdf_gen.page_generator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', dest='input_dir', action='store', default='data/hocr_example')
    parser.add_argument('--input-pdf', dest='input_pdf', action='store')
    parser.add_argument('--outfile', dest='outfile', action='store')
    args = parser.parse_args()
    tag(
        package=pdf_gen.ocr_dir.resolve(args.input_dir),
        input_pdf=args.input_pdf,
        out_filename=args.outfile,
    )


def tag(package: pdf_gen.ocr_dir.Package, input_pdf: str, out_filename: str):
    # Map page labels to actual indices
    page_mapping = {}
    toc = None
    for i, page in enumerate(pdf_gen.mets_parser.iter_pages(str(package.mets))):
        if page.order_label:
            page_mapping[page.order_label] = i
        if page.is_toc:
            toc = i

    if toc is None:
        return

    print("Creating Table of Contents")
    reader = pypdf.PdfReader(input_pdf)
    writer = pypdf.PdfWriter()
    # I know, we're doing this twice, w/e
    parsed_pages = list(pdf_gen.mets_parser.iter_pages(str(package.mets)))
    toc_page = reader.pages[toc]
    parsed_page = parsed_pages[toc]
    if not pdf_gen.mets_parser.is_djvu_xml(package.page_file(parsed_page.ocr_file.location)):
        print("TOC only supported for DjVu thus far")
        return

    for p in reader.pages:
        writer.add_page(p)
    for toc_entry in pdf_gen.djvu_generator.iter_toc_data(str(package.page_file(parsed_page.ocr_file.location))):
        page_order = page_mapping.get(toc_entry.order_label)
        if not page_order:
            continue
        print(f"Writing TOC entry {toc_entry.order_label} at page index {page_order}")
        annotation = AnnotationBuilder.link(
            rect=(toc_entry.x1, toc_entry.y1, toc_entry.x2, toc_entry.y2),
            target_page_index=page_order,
        )
        writer.add_annotation(page_number=toc, annotation=annotation)
        writer.add_named_destination(title=f"Chapter {toc_entry.order_label}", page_number=page_order)

    with open(out_filename, "wb") as final_pdf:
        writer.write(final_pdf)


if __name__ == "__main__":
    main()
