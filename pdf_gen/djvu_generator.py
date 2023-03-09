import dataclasses
import typing

from lxml import etree
from reportlab.pdfgen import canvas


@dataclasses.dataclass
class Word:
    w: str
    x1: int
    y1: int
    x2: int
    y2: int



def generate_pdf_page(djvu_filename: str, image_filename: str, out_filename: str):
    tree = etree.parse(djvu_filename)
    root = tree.getroot()
    obj = root.find(".//OBJECT")
    page_height = int(obj.get("height"))
    page_width = int(obj.get("width"))
    dpi = 300
    for param in root.findall(".//PARAM"):
        if param.get("name") == "DPI":
            dpi = int(param.get("value"))

    pdf = canvas.Canvas(out_filename, pagesize=(page_width, page_height), pageCompression=1)
    pdf.drawImage(image_filename, 0, 0, width=page_width, height=page_height)
    for words in _iterlines(root):
        for word in words:
            text = pdf.beginText()
            text.setTextRenderMode(3)
            # Note this doesn't account for if the words are angled, but I don't
            # think these files contain enough information to do something about
            # that!
            fontsize = word.y2 - word.y1
            text.setFont("Helvetica", fontsize)
            text.setTextOrigin(word.x1, page_height - word.y1)
            text.textOut(word.w)
            pdf.drawText(text)

    pdf.showPage()
    pdf.save()


def _iterlines(root) -> typing.Iterator[list[Word]]:
    for line_node in root.findall(".//LINE"):
        yield list(_iterwords(line_node))


def _iterwords(root) -> typing.Iterator[Word]:
    for word_node in root.findall(".//WORD"):
        coords_str = word_node.get("coords")
        x1, y1, x2, y2 = coords_str.split(",")
        yield Word(w=word_node.text, x1=int(x2), y1=int(y1), x2=int(x2), y2=int(y2))
