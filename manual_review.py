"""Сохранённые результаты ручного просмотра фотографий.

Привязка к строке, исходному названию и URL защищает от повторного
применения к другому товару или новой фотографии в каталоге.
"""
from __future__ import annotations
import csv
from pathlib import Path
from matching_engine import Match

MANUAL_FILE="Ручная проверка фотографий.csv"
VALID={"Совпадает", "Частично", "Неясно", "Ошибка"}

def load_manual(path: str=MANUAL_FILE) -> dict[int,dict[str,str]]:
    if not Path(path).exists():return {}
    with open(path,encoding="utf-8-sig",newline="") as file:
        records=list(csv.DictReader(file,delimiter=";"))
    result={}
    for record in records:
        try: row=int(record["Строка Excel"])
        except (ValueError,KeyError):continue
        if record.get("Решение") not in VALID:continue
        if row in result:raise ValueError(f"Повтор строки {row} в ручном журнале")
        result[row]=record
    return result

def apply_manual(row:int,name:str,result:Match,
                 manual:dict[int,dict[str,str]]) -> tuple[Match,str,str]:
    review=manual.get(row)
    if not review or not result.product:
        return result,"",""
    if review["Товар из ведомости"]!=name or review["URL фотографии"]!=result.product.url:
        return result,"",""
    decision=review["Решение"]
    description=review.get("Комментарий","")
    if decision=="Ошибка":
        return (Match(None,result.score,"Нет совпадения",
                      "РУЧНАЯ ПРОВЕРКА ФОТОГРАФИИ: "+description,
                      result.alternatives),decision,description)
    if decision in ("Неясно","Частично") and result.status in ("Надёжно","Вероятно"):
        result=Match(result.product,result.score,"Проверить",
                     result.reason+". Ручная проверка: "+description,
                     result.alternatives)
    return result,decision,description
