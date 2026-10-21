"""Заполнить фотографии в Движении товара по каталогам Garfield.

Запуск: python3 merger.py
Никаких обязательных сторонних модулей и сетевых запросов.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from pathlib import Path

from matching_engine import Matcher, Match, build_product
from rescue_matching import rescue
from anchor_matching import anchor_match
from page_validation import page_discrepancy
from manual_review import load_manual, apply_manual
from sitemap_matching import SitemapMatcher
from matching_engine import build_product as create_catalog_product
from spreadsheet_io import read_first_sheet, update_xlsx

DEFAULT_INPUT = "Движение товара.xlsx"
DEFAULT_CATALOGS = tuple(f"products_garfield_{i}.xlsx" for i in range(1,4))
DEFAULT_OUTPUT = "Движение товара с фотографиями.xlsx"
REVIEW_FILE = "Товары для проверки.csv"
REPORT_FILE = "Отчёт о сопоставлении.csv"
AUDIT_FILE = "Проверка страниц товаров.csv"
SITEMAP_CACHE = "Найденные фото Garfield.csv"
SITEMAP_FILE = "sitemap_img.xml"

def load_sitemap_cache(path: str = SITEMAP_CACHE) -> dict[int, dict[str,str]]:
    if not Path(path).is_file():
        return {}
    with open(path,encoding="utf-8-sig",newline="") as f:
        return {int(row["Строка Excel"]):row for row in csv.DictReader(f,delimiter=";")}

def cache_match(row_number: int,name: str,
                cache: dict[int,dict[str,str]]):
    from matching_engine import Match
    cached=cache.get(row_number)
    if not cached or cached.get("Товар из ведомости")!=name:
        return None
    url=cached.get("URL фотографии","")
    page=cached.get("URL товара","")
    title=cached.get("Товар из каталога","")
    if not (url.startswith("https://garfield.by/") and
            page.startswith("https://garfield.by/catalog/")):
        return None
    product=create_catalog_product(row_number,title,url,"",page)
    return Match(product,float(cached["Оценка"]),"Проверить",
                 "Ранее найденная официальная фотография Garfield. Проверьте фасовку.",
                 ())

def clean(value: str) -> str:
    return " ".join(str(value or "").split())

def read_catalogs(paths: list[str]) -> list:
    catalog=[]
    for path in paths:
        file=Path(path)
        if not file.is_file():
            raise FileNotFoundError(f"Не найден каталог: {file}")
        headers={}
        added=0
        for record in read_first_sheet(file):
            if record.row==1:
                headers={clean(v):k for k,v in record.data.items()}
                for required in ("Название","URL Картинки в S3"):
                    if required not in headers:
                        raise ValueError(f"В каталоге {file} нет поля {required}")
                continue
            get=lambda name: clean(record.data.get(headers.get(name,""),""))
            item=build_product(record.row, get("Название"),
                               get("URL Картинки в S3"), get("Артикул"),
                               get("URL Товара"),get("Категория"))
            if item.name and item.url:
                catalog.append(item)
                added+=1
        print(f"Каталог {file.name}: {added} записей")
    return catalog

def run(source: str = DEFAULT_INPUT, catalogs: list[str] | None = None,
        output: str = DEFAULT_OUTPUT) -> dict[str,int]:
    if not Path(source).is_file():
        raise FileNotFoundError(f"Нет исходной таблицы: {source}")
    items=read_catalogs(catalogs or list(DEFAULT_CATALOGS))
    if not items:
        raise ValueError("Каталоги пусты")
    matcher=Matcher(items)
    sitemap=SitemapMatcher(SITEMAP_FILE) if Path(SITEMAP_FILE).exists() else None
    cached_images=load_sitemap_cache()
    manual_reviews=load_manual()
    checked_rows=Counter()
    new_cache=[]
    print(f"Готово к поиску: {len(matcher.catalog)} товаров каталога")
    statistics=Counter()
    results={}
    report=[]
    review=[]
    discrepancies=[]
    for row in read_first_sheet(source):
        if row.row<=3:
            continue
        name=clean(row.data.get("A",""))
        if not name or name.lower().startswith(("итого", "всего")):
            continue
        source_product=build_product(row.row,name)
        result=matcher.match(source_product)
        result=rescue(matcher,source_product,result)
        image_source="Каталоги Garfield (S3)" if result.product else ""
        if not result.product:
            anchor=anchor_match(matcher,source_product)
            if anchor:
                result=anchor
                image_source="Каталоги Garfield (по редкой серии)"
        if not result.product:
            new_result=(sitemap.match(source_product) if sitemap else None)
            if not new_result:
                new_result=cache_match(row.row,name,cached_images)
            if new_result and new_result.product:
                result=new_result
                image_source="Официальный сайт Garfield"
        if result.product and result.product.product_url:
            issue=page_discrepancy(source_product,result.product.product_url)
            if issue:
                discrepancies.append({
                    "Строка Excel":row.row,
                    "Товар из ведомости":name,
                    "Предложенный товар":result.product.name,
                    "Ссылка на страницу":result.product.product_url,
                    "Предложенная фотография":result.product.url,
                    "Выявленное несоответствие":issue
                })
                result=Match(None,result.score,"Нет совпадения",
                             "ПРОВЕРКА ФАКТИЧЕСКОЙ КАРТОЧКИ: " + issue,
                             result.alternatives)
                image_source=""
        result, manual_status, manual_comment=apply_manual(row.row,name,result,manual_reviews)
        if manual_status:
            checked_rows[manual_status]+=1
            if manual_status=="Ошибка":
                image_source=""
        if image_source=="Официальный сайт Garfield" and result.product:
            new_cache.append({"Строка Excel":row.row,
                              "Товар из ведомости":name,
                              "Товар из каталога":result.product.name,
                              "URL фотографии":result.product.url,
                              "URL товара":result.product.product_url,
                              "Оценка":round(result.score,4)})
        statistics[result.status]+=1
        candidate=result.product
        result_row={
            "url":candidate.url if candidate else "",
            "status":result.status,
            "confidence":round(result.score,4),
            "catalog_name":candidate.name if candidate else "",
            "sku":candidate.sku if candidate else "",
            "product_url":candidate.product_url if candidate else "",
            "reason":result.reason,
            "image_source":image_source,
            "manual_status":manual_status,
            "manual_comment":manual_comment
        }
        results[row.row]=result_row
        record={
            "Строка Excel":row.row,
            "Товар из ведомости":name,
            "Статус":result.status,
            "Оценка":round(result.score,4),
            "Товар из каталога":result_row["catalog_name"],
            "Артикул":result_row["sku"],
            "URL фотографии":result_row["url"],
            "Источник фотографии":image_source,
            "URL Товара":result_row["product_url"],
            "Причина":result_row["reason"],
            "Ручная проверка":manual_status,
            "Примечание ручной проверки":manual_comment,
            "Другие кандидаты":" | ".join(
                f"{score:.3f}: {alternative.name} [{alternative.sku}]"
                for score,alternative in result.alternatives[1:4])
        }
        report.append(record)
        if result.status not in ("Надёжно","Вероятно"):
            review.append(record)
        if len(results)%250==0:
            print(f"Обработано {len(results)} товаров")
    update_xlsx(source,output,results)
    if discrepancies:
        with open(AUDIT_FILE,"w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(discrepancies[0]),delimiter=";")
            writer.writeheader()
            writer.writerows(discrepancies)
    if sitemap is not None:
        with open(SITEMAP_CACHE,"w",encoding="utf-8-sig",newline="") as cache_file:
            writer=csv.DictWriter(cache_file,fieldnames=[
                "Строка Excel","Товар из ведомости","Товар из каталога",
                "URL фотографии","URL товара","Оценка"],delimiter=";")
            writer.writeheader()
            writer.writerows(new_cache)
    columns=list(report[0]) if report else []
    for path, rows in ((REPORT_FILE,report),(REVIEW_FILE,review)):
        with open(path,"w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=columns,delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
    total=sum(statistics.values())
    filled=sum(v for k,v in statistics.items() if k in ("Надёжно","Вероятно","Проверить"))
    print("Всего позиций:",total)
    print("С фотографиями:",filled)
    for status,count in sorted(statistics.items()):
        print(f"{status}: {count}")
    with open("Итоги подбора фотографий.txt", "w", encoding="utf-8") as summary:
        summary.write(f"Всего товарных строк: {total}\n")
        summary.write(f"С подобранной фотографией: {filled}\n")
        for status, count in sorted(statistics.items()):
            summary.write(f"{status}: {count}\n")
        summary.write("Статус Проверить означает, что ссылка предварительная и может быть ошибочной.\n")
        summary.write("Каталоги часто не указывают размер упаковки.\n")
        summary.write(f"Из официальной карты сайта Garfield: {len(new_cache)}\n")
        summary.write(f"Несовпадения по страницам магазина (фото исключены): {len(discrepancies)}\n")
        summary.write(f"Ручных проверок фотографий в журнале: {len(manual_reviews)}\n")
        summary.write(f"Результатов ручной проверки, применённых к текущему файлу: {sum(checked_rows.values())}\n")
        for decision,count in sorted(checked_rows.items()):
            summary.write(f"  Ручная проверка, {decision}: {count}\n")
    print("Созданы:",output, REPORT_FILE, REVIEW_FILE, "Итоги подбора фотографий.txt")
    return dict(statistics)

def main() -> None:
    parser=argparse.ArgumentParser(description="Подбор фотографий для товаров из Excel")
    parser.add_argument("--input",default=DEFAULT_INPUT,help="Исходная таблица")
    parser.add_argument("--catalog",action="append",help="Файл каталога, можно указывать несколько раз")
    parser.add_argument("--output",default=DEFAULT_OUTPUT,help="Имя полученного Excel")
    args=parser.parse_args()
    run(args.input,args.catalog,args.output)

if __name__=="__main__":
    main()
