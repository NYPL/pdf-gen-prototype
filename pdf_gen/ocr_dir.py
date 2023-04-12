import dataclasses
import os
import pathlib


@dataclasses.dataclass
class Package:
    mets: pathlib.Path
    ocr_metadata: pathlib.Path
    page_dir: pathlib.Path

    def page_file(self, loc: str) -> pathlib.Path:
        return self.page_dir.joinpath(loc)


def resolve(input_dir: str) -> Package:
    path = pathlib.Path(input_dir)
    mets = next(x for x in path.iterdir() if x.is_file() and x.suffixes == [".mets", ".xml"])
    page_dir = next(x for x in path.iterdir() if x.is_dir())
    ocr_metadata = next(
        x for x in page_dir.iterdir() if x.is_file() and x.stem.endswith(page_dir.stem)
    )
    return Package(
        mets=mets,
        ocr_metadata=ocr_metadata,
        page_dir=page_dir,
    )
