#!/usr/bin/python


from typing import Iterator

import json
import hashlib
import urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


LOCALDIR = Path(__file__).parent
INDEX_PATH = LOCALDIR / "MusopenCollectionAsFlac_files.xml"
MASTER_DOWNLOAD_URL = r"https://archive.org/download/MusopenCollectionAsFlac"


class FlacFile:
    def __init__(self, file_xml_element: Element):
        self.element = file_xml_element
        self.musopen_naming = self.element.attrib["name"]

        self.composer, self.piece = self.musopen_naming.split("/")

        self.composer_dir_path = LOCALDIR / self.composer
        self.piece_path = self.composer_dir_path / self.piece
        self.download_url = f"{MASTER_DOWNLOAD_URL}/{self.musopen_naming}"

    @property
    def md5(self) -> str | None:
        for child in self.element:
            if child.tag == "md5":
                return child.text

    def create_composer_dir_path(self):
        if self.composer_dir_path.exists():
            print(f"Composer directory {self.composer} already exists")
            return

        print(f"Creating composer directory {self.composer}")
        self.composer_dir_path.mkdir()

    def is_piece_downloaded(self) -> bool:
        if not self.piece_path.exists():
            return False

        piece_hash = hashlib.md5(self.piece_path.read_bytes()).hexdigest()
        return piece_hash.lower() == self.md5.lower()

    def download_piece(self):
        if self.is_piece_downloaded():
            print(f"Already downloaded {self.musopen_naming}")
            return

        print(f"Downloading {self.download_url}")
        urllib.request.urlretrieve(self.download_url, self.piece_path)

        if self.is_piece_downloaded():
            print(f"Verified {self.musopen_naming}")
        else:
            print(f"Error downloading {self.musopen_naming}")

    def serialize(self) -> dict:
        return {
            "composer": self.composer,
            "piece": self.piece,
            "md5": self.md5,
            "download_url": self.download_url,
        }

    @staticmethod
    def is_flac(file_xml_element: Element) -> bool:
        return file_xml_element.attrib["name"].endswith(".flac")


class MusopenCollection:
    def __init__(self, xml_index_path: Path):
        self.tree = ET.parse(xml_index_path)
        self.root = self.tree.getroot()

    @property
    def _file_xml_elements(self) -> Iterator[Element]:
        for child in self.root:
            if child.tag == "file":
                yield child

    @property
    def flac_files(self) -> Iterator[FlacFile]:
        for fe in self._file_xml_elements:
            if FlacFile.is_flac(fe):
                yield FlacFile(fe)


if __name__ == "__main__":
    collection = MusopenCollection(INDEX_PATH)
    for flac_file in collection.flac_files:
        print(json.dumps(flac_file.serialize(), indent=2))
        flac_file.create_composer_dir_path()
        flac_file.download_piece()
        print()
