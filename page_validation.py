"""Проверка веса и формы товара по АДРЕСУ конкретной страницы магазина.

Это только свидетельство явного противоречия. Если веса в адресе нет,
отсутствие ошибки не означает, что фото подтверждено.
"""
from __future__ import annotations
import re
from urllib.parse import unquote,urlsplit
from matching_engine import units,Product

WEIGHT = re.compile(r"(?:^|-)(\d{1,5})(?:-(\d{1,2}))?-(kg|gr|g|ml|l)(?=-|\.|$)")
MULTIPACK = re.compile(r"(\d+)-sht-kh-(\d+)-(?:gr|g)(?:\.|$)")
RANGE = re.compile(r"\d{1,2}-\d{1,2}-\d{1,2}-(?:kg|l)(?:-|\.|$)")

def page_discrepancy(source: Product, url: str) -> str | None:
    page=unquote(urlsplit(url).path.lower())
    if not url or not page.endswith(".html"):
        return None
    slug=page.rsplit("/",1)[-1].removesuffix(".html")
    if not slug:
        return None
    if "/konservyi" in page or slug.startswith("konservy-"):
        if "dry" in source.tokens or "сухой" in source.tokens:
            return "сухой корм связан с карточкой консервов"
    if "/suhie-korma" in page or "/sukhie-korma" in page:
        if "wet" in source.tokens or "влажный" in source.tokens or "pouch" in source.tokens:
            return "влажный корм связан с карточкой сухого корма"
    if RANGE.search(slug):
        return None
    source_sizes=units(source.name)
    pairs=list(WEIGHT.finditer(slug))
    for match in pairs:
        major,minor,suffix=match.groups()
        if minor:
            number=float(f"{int(major)}.{minor}")
        elif len(major)==2 and major.startswith("0") and suffix in ("kg","l"):
            number=int(major)/10
        else:
            number=float(major)
        family="mass" if suffix in ("kg","g","gr") else "volume"
        page_amount=number*1000 if suffix in ("kg","l") else number
        multiple=MULTIPACK.search(slug)
        if multiple and family=="mass":
            page_amount=float(multiple.group(1))*float(multiple.group(2))
        expected={v for kind,v in source_sizes if kind==family}
        if not expected:
            continue
        # Match an explicitly stated total, not a broad "same product line".
        if all(abs(v-page_amount)>max(.02,.005*max(v,page_amount)) for v in expected):
            return (f"на странице указано {page_amount:g} " +
                    ("г" if family=="mass" else "мл") +
                    ", в ведомости " + "/".join(f"{v:g}" for v in sorted(expected)) +
                    (" г" if family=="mass" else " мл"))
    return None
