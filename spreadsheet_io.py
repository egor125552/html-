"""Чтение и дополнение XLSX без изменения исходных листов и формул."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterator
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
M = "{" + NS + "}"
ET.register_namespace("", NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")
ET.register_namespace("x14ac", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac")

@dataclass(frozen=True)
class Record:
    row: int
    data: dict[str, str]

def _cell_column(address: str) -> str:
    found = re.match(r"[A-Z]+", address or "")
    return found.group(0) if found else ""

def _shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in item.iter(M + "t"))
            for item in root.findall(M + "si")]

def read_first_sheet(path: str | Path) -> Iterator[Record]:
    with ZipFile(path) as archive:
        strings = _shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for row in sheet.findall(".//" + M + "sheetData/" + M + "row"):
            cells: dict[str, str] = {}
            for cell in row.findall(M + "c"):
                col = _cell_column(cell.get("r", ""))
                kind = cell.get("t")
                value = cell.find(M + "v")
                inline = cell.find(M + "is")
                if kind == "s" and value is not None and value.text:
                    text = strings[int(value.text)]
                elif inline is not None:
                    text = "".join(t.text or "" for t in inline.iter(M + "t"))
                else:
                    text = value.text if value is not None else ""
                cells[col] = text or ""
            yield Record(int(row.get("r", "0")), cells)

def update_xlsx(source: str | Path, output: str | Path, matches: dict[int, dict[str, str | float]]) -> None:
    """Создать новую копию книги, не трогая исходные 12 столбцов."""
    names = ["URL фотографии", "Статус проверки", "Уверенность",
             "Название в каталоге", "Артикул", "URL товара", "Обоснование", "Источник фотографии",
             "Ручная проверка", "Комментарий ручной проверки"]
    columns = ["M", "N", "O", "P", "Q", "R", "S", "T", "U", "V"]
    with ZipFile(source) as zin:
        root = ET.fromstring(zin.read("xl/worksheets/sheet1.xml"))
        dimension = root.find(M + "dimension")
        if dimension is not None:
            current = dimension.get("ref", "A1:L2152")
            m = re.search(r"(\d+)$", current)
            dimension.set("ref", f"A1:V{m.group(1) if m else '2152'}")
        column_definitions = root.find(M + "cols")
        if column_definitions is None:
            column_definitions = ET.Element(M + "cols")
            data_node = root.find(M + "sheetData")
            root.insert(list(root).index(data_node), column_definitions)
        for col_index, width in ((13, 49), (14, 18), (15, 15), (16, 46),
                                 (17, 20), (18, 48), (19, 45), (20, 23), (21, 21), (22, 66)):
            ET.SubElement(column_definitions, M + "col", {
                "min": str(col_index), "max": str(col_index),
                "width": str(width), "customWidth": "1"
            })
        data = root.find(M + "sheetData")
        if data is None:
            raise ValueError("В книге нет листа с таблицей")
        for row in data.findall(M + "row"):
            row_number = int(row.get("r", "0"))
            if row_number == 1:
                values: list[str | float] = ["Фотография", "Проверка", "Проверка",
                                             "Проверка", "Проверка", "Проверка", "Проверка", "Проверка", "Проверка", "Проверка"]
            elif row_number == 2:
                values = names
            else:
                match = matches.get(row_number, {})
                values = [match.get(k, "") for k in
                          ("url", "status", "confidence", "catalog_name", "sku", "product_url", "reason", "image_source",
                           "manual_status", "manual_comment")]
            for column, value in zip(columns, values):
                if value == "" or value is None:
                    continue
                attributes = {"r": f"{column}{row_number}"}
                if row_number in (1, 2):
                    original = next((c for c in row.findall(M + "c")
                                     if c.get("r") == f"A{row_number}"), None)
                    if original is not None and original.get("s") is not None:
                        attributes["s"] = original.get("s")
                cell = ET.SubElement(row, M + "c", attributes)
                if isinstance(value, (int, float)):
                    ET.SubElement(cell, M + "v").text = str(value)
                else:
                    cell.set("t", "inlineStr")
                    ET.SubElement(ET.SubElement(cell, M + "is"), M + "t").text = str(value)
            if row_number > 2 and matches.get(row_number):
                status = matches[row_number].get("status")
                if status:
                    row.set("spans", "1:22")
        xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        with ZipFile(output, "w") as zout:
            for file_info in zin.infolist():
                if file_info.filename == "xl/worksheets/sheet1.xml":
                    zout.writestr(file_info, xml)
                else:
                    zout.writestr(file_info, zin.read(file_info.filename))
    with ZipFile(output) as check:
        assert check.testzip() is None
        ET.fromstring(check.read("xl/worksheets/sheet1.xml"))
