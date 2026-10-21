"""Дополнительный источник: официальный публичный список фотографий Garfield."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

from matching_engine import Match, Matcher, Product, build_product
from rescue_matching import evidence_for

CYRILLIC=dict(zip(
    "абвгдежзийклмнопрстуфхцчшщъыьэюя",
    ("a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o",
     "p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya")
))
TOKEN_MAP={
    "korm":"food","sukhoy":"dry","sukhie":"dry",
    "konservy":"wet","konservy":"wet","konserva":"wet",
    "pauch":"pouch","pashtet":"pate","lakomstvo":"treat",
    "dlya":"","v":"","s":"","so":"","i":"","iz":"","na":"",
    "sobak":"dog","sobaki":"dog","sobakami":"dog","psov":"dog",
    "koshek":"cat","koshki":"cat","kotov":"cat","kotyat":"kitten",
    "shchenkov":"puppy","shchenki":"puppy","zhivotnykh":"animals",
    "indeyka":"turkey","indeykoy":"turkey","indeyki":"turkey",
    "kuritsa":"chicken","kuritsey":"chicken","kuritsy":"chicken",
    "tsyplyonok":"chicken","tsyplenok":"chicken","utka":"duck","utkoy":"duck",
    "govyadina":"beef","govyadinoy":"beef","govyadiny":"beef",
    "yagnenok":"lamb","yagnenkom":"lamb","yagn":"lamb",
    "losos":"salmon","lososem":"salmon","lososya":"salmon",
    "krolik":"rabbit","krolikom":"rabbit","krolika":"rabbit",
    "tunets":"tuna","tuntsa":"tuna","krevetka":"shrimp","krevetkami":"shrimp",
    "ryba":"fish","ryboy":"fish","ryby":"fish",
    "serdtse":"heart","kartofel":"potato","ris":"rice","risom":"rice",
    "souse":"gravy","sous":"gravy","zhele":"jelly",
    "chereshnya":"cherry","siniy":"blue","krasnyy":"red",
    "zelenyy":"green","chernyy":"black","belyy":"white",
    "rozovyy":"pink","zheltyy":"yellow","goluboy":"lightblue",
    "sterilizovannykh":"sterilised","vzroslykh":"adult",
    "vzroslyy":"adult","melkikh":"small","krupnykh":"large",
    "porod":"breed","srednikh":"medium","miniatyurnykh":"small",
    "sob":"dog","kot":"cat"
}
FILLER={"dlya","v","s","so","i","iz","na","the","of","and","a","po"}
SPECIES={"cat","dog","fish","bird","rodent","horse"}
SITEMAP_NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9',
            'i':'http://www.google.com/schemas/sitemap-image/1.1'}

def latin(text: str) -> str:
    return "".join(CYRILLIC.get(ch,ch) for ch in text.lower().replace("ё","е"))

def canonical_title(text: str) -> str:
    base=latin(text)
    words=re.findall(r"[a-z0-9]+",base)
    return " ".join(TOKEN_MAP.get(w,w) for w in words if w not in FILLER).strip()

def prepare(source: Product) -> Product:
    # Keep original weight, age, breed and safety attributes.
    normalized=canonical_title(source.normalized)
    return replace(source,normalized=normalized,
                   tokens=frozenset(w for w in normalized.split() if len(w)>1))

def image_records(xmlfile: str | Path) -> list[Product]:
    if not Path(xmlfile).exists():
        return []
    root=ET.parse(xmlfile).getroot()
    results=[]
    seen=set()
    for element in root.findall('s:url',SITEMAP_NS):
        page=element.findtext('s:loc',default="",namespaces=SITEMAP_NS)
        if page in seen or urlparse(page).netloc not in ('garfield.by','www.garfield.by'):
            continue
        images=[loc.text for loc in element.findall('i:image/i:loc',SITEMAP_NS)
                if loc.text and urlparse(loc.text).netloc in ('garfield.by','www.garfield.by')]
        if not images:
            continue
        slug=unquote(urlparse(page).path.rsplit("/",1)[-1].removesuffix(".html"))
        title=canonical_title(slug.replace("-"," "))
        category="cat" if "/cats/" in page else "dog" if "/dogs/" in page else ""
        if not title:
            continue
        item=build_product(len(results)+1,title,images[0],"",page,category)
        seen.add(page)
        results.append(item)
    return results

class SitemapMatcher:
    def __init__(self,xmlfile: str | Path):
        self.catalog=image_records(xmlfile)
        self.matcher=Matcher(self.catalog) if self.catalog else None

    def match(self,source: Product) -> Match | None:
        if self.matcher is None:
            return None
        canonical=prepare(source)
        preliminary=self.matcher.match(canonical,candidate_limit=250)
        if preliminary.product is None:
            return None
        if preliminary.score<.60:
            return None
        candidate=preliminary.product
        if "pate" in source.tokens and "pate" not in candidate.tokens:
            return None
        if "wet" in source.tokens and "dry" in candidate.tokens:
            return None
        if "dry" in source.tokens and "wet" in candidate.tokens:
            return None
        # Require high-confidence identity clues beyond an animal, food type or colour.
        proof=evidence_for(self.matcher,canonical,candidate)
        if not proof.accepted:
            return None
        # Even a high match to the URL slug does not prove pack artwork is identical.
        return Match(candidate,preliminary.score,"Проверить",
             "Фото из официальной карты Garfield. Совпадение названия страницы; " +
             proof.reason + ". Проверить фасовку и картинку.",
             preliminary.alternatives)
