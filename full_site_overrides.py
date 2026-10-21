"""Individually inspected official-site product photo overrides."""
from __future__ import annotations
import csv
from pathlib import Path
from urllib.parse import urlsplit
from matching_engine import Match,build_product
from page_validation import page_discrepancy

FILE="Подтверждённые фотографии из полного каталога.csv"

def load_site_matches(path: str=FILE) -> dict[int,dict[str,str]]:
    if not Path(path).exists():return {}
    with open(path,encoding="utf-8-sig",newline="") as f:
        entries=list(csv.DictReader(f,delimiter=";"))
    result={}
    for row in entries:
        number=int(row["Строка Excel"])
        if number in result:raise ValueError("Повтор строки в полном каталоге")
        result[number]=row
    return result

def verified_page_match(row_number:int,original_name:str,original_product,
                        earlier_manual:dict[str,str]|None,
                        cache:dict[int,dict[str,str]]) -> tuple[Match,str,str] | None:
    item=cache.get(row_number)
    if not item or item["Товар из ведомости"]!=original_name:
        return None
    image=item["URL фотографии"]
    page=item["URL товара"]
    if not page.startswith("https://garfield.by/catalog/"):
        return None
    if urlsplit(image).scheme!="https" or urlsplit(image).netloc not in (
        "garfield.by","io.activecloud.com"):
        return None
    if earlier_manual and earlier_manual.get("Решение")=="Ошибка":
        if earlier_manual.get("URL фотографии")==image:
            return None
    if page_discrepancy(original_product,page):
        return None
    caption=item["Товар из каталога"]
    comment=item["Основание ручной проверки"]
    if not comment:return None
    prod=build_product(row_number,caption,image,"",page)
    return (Match(prod,float(item["Оценка"]),"Проверить",
           "Новая карточка из полной карты Garfield, фотография просмотрена. "+comment),
           "Частично",comment)
