import dataclasses
import typing

from lxml import etree
from lxml import html

# https://github.com/ocrmypdf/OCRmyPDF/issues/453#issuecomment-761254016
DOCTYPE = """<!DOCTYPE html [<!ENTITY shy "&#173;"> <!ENTITY thinsp "&#2009;">]>"""

NSMAP = {
    "METS": "http://www.loc.gov/METS/",
    "xlink": "http://www.w3.org/1999/xlink",
}


@dataclasses.dataclass
class FileDef:
    fid: str
    mime_type: str
    location: str
    use: str


@dataclasses.dataclass
class Page:
    image_file: FileDef
    ocr_file: FileDef


def iter_pages(file_location: str) -> typing.Iterator[Page]:
    tree = etree.parse(file_location)
    yield from _iter_pages(tree)


def is_djvu_xml(ocr_file_location: str) -> bool:
    # Just have to inspect the file directly unfortunately
    with open(ocr_file_location, "r") as f:
        for line in f.readlines():
            if line.strip() == "<!DOCTYPE DjVuXML>":
                return True


def reset_hocr_doctype(ocr_file_location: str, outfile_location: str) -> None:
    parser = etree.HTMLParser()
    tree = etree.parse(ocr_file_location, parser=parser)
    ocr_string = etree.tostring(
        tree,
        pretty_print=True,
        xml_declaration=True,
        doctype=DOCTYPE,
    )
    # For some horrible reason, the `tostring` method does the following:
    #   - if xml_declaration is True and there is a DOCTYPE, it sandwiches the DOCTYPE between the
    #     existing declaration and the new one
    #   - if xml_declaration is False and there is a DOCTYPE, it keeps the existing declaration and
    #     and places the doctype on top
    #   - and weirdest of all, if xml_declaration is False and there is no doctype set, it swaps
    #     the existing doctype and declaration, again rendering the document unparseable
    # So just do the first case and throw out the 3rd line (the original declaration)
    ocr_string = b'\n'.join(line for i, line in enumerate(ocr_string.split(b'\n')) if i != 2)
    with open(outfile_location, "wb") as f:
        f.write(ocr_string)


def _iter_pages(tree: etree) -> typing.Iterator[Page]:
    """Return an ordered sequence of pages"""
    struct_map = tree.getroot().find("METS:structMap", namespaces=NSMAP)
    file_mapping = _map_file_ids(tree)
    for page in struct_map.find("METS:div", namespaces=NSMAP).findall("METS:div", namespaces=NSMAP):
        if not page.get("TYPE") == "page":
            continue

        yield _parse_page(page, file_mapping)


def _parse_page(page_elem, file_mapping) -> Page:
    image_file = next(
        file_mapping[fptr.get("FILEID")]
        for fptr in page_elem.findall("METS:fptr", namespaces=NSMAP)
        if file_mapping[fptr.get("FILEID")].use == "image"
    )
    ocr_file = next(
        file_mapping[fptr.get("FILEID")]
        for fptr in page_elem.findall("METS:fptr", namespaces=NSMAP)
        if file_mapping[fptr.get("FILEID")].use == "coordOCR"
    )

    return Page(image_file=image_file, ocr_file=ocr_file)


def _map_file_ids(tree: etree) -> dict[str, FileDef]:
    id_map = {}
    file_sec = tree.getroot().find("METS:fileSec", namespaces=NSMAP)
    for group in file_sec.findall("METS:fileGrp", namespaces=NSMAP):
        use = group.get("USE")
        for file in group.findall("METS:file", namespaces=NSMAP):
            file_id = file.get("ID")
            location = file.find("METS:FLocat", namespaces=NSMAP).xpath("@xlink:href", namespaces=NSMAP)[0]
            id_map[file_id] = FileDef(
                fid=file_id,
                mime_type=file.get("MIMETYPE"),
                location=location,
                use=use,
            )

    return id_map
