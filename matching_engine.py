"""Независимый модуль сравнения товаров: сначала признаки, затем похожесть."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from math import log
import re
import unicodedata
from urllib.parse import urlparse
from identity_safety import conflicts as identity_conflicts

ALIASES = {
    "нэйчес протекшн":"natures protection", "нейчерс протекшн":"natures protection",
    "нэчес протекшн":"natures protection", "роял канин":"royal canin",
    "хиллс":"hills", "баунтифул кэтч":"bountiful catch", "эйджинг":"ageing", "хьюлс":"hills", "монж":"monge",
    "брит кеа":"brit care", "брит":"brit", "фармина":"farmina",
    "хэппи дог":"happy dog", "хэппи кэт":"happy cat",
    "пурина про план":"purina pro plan", "про план":"pro plan",
    "пурина":"purina", "н д":"farmina nd", "н&д":"farmina nd", "nature s":"natures", "акана":"acana", "ориджен":"orijen",
    "джосера":"josera", "фитмин":"fitmin", "бош":"bosch",
    "эукануба":"eukanuba", "альфапет":"alphapet",
    "амброзия":"ambrosia", "вискас":"whiskas",
    "грандорф":"grandorf", "бруксфилд":"brooksfield",
    "сириус":"sirius", "чекопи":"chicopee", "чикопи":"chicopee", "кэа":"care", "кэт":"cat", "дог":"dog",
    "мнямс":"mnyams", "нямс":"mnyams", "wanpy":"wanpy", "ванпи":"wanpy", "бубу":"bubu", "кормовая добавка":"supplement", "клини":"cliny", "флекси":"flexi",
    "фурминатор":"furminator", "фурпласт":"ferplast",
    "ферпласт":"ferplast", "деревенские лакомства":"derevenskie lakomstva",
    "литл ван":"little one", "банни":"bunny",
    "триол":"triol", "гамма":"gamma", "санабелль":"sanabelle",
    "апиценна":"apicenna", "празицид":"prazicid",
    "дронтал":"drontal", "барс":"bars", "ролф клуб":"rolf club",
    "зооник":"zoonik", "петс":"pets", "петлайн":"petline",
    "грин кьюзин":"green qzin", "молина":"molina",
    "аймак":"imac", "коллар":"collar", "харпер":"harper",
    "шезир":"schesir", "сибау":"cibau", "забота":"care",
    "nature s":"natures", "natures":"natures",
    "д кош":"cat", "д кошек":"cat", "д кот":"cat", "д кота":"cat", "д к":"cat", "д соб":"dog", "д с":"dog", "котята":"kitten", "д/щенков":"puppy", "д/котят":"kitten", "котят":"kitten",
    "кошек":"cat", "кошки":"cat", "кошкам":"cat", "кота":"cat", "котов":"cat",
    "коты":"cat", "кот":"cat", "cats":"cat",
    "собакам":"dog", "собак":"dog", "собаки":"dog", "соб":"dog",
    "собака":"dog", "dogs":"dog", "щенков":"puppy", "щенка":"puppy",
    "щенки":"puppy", "котенок":"kitten", "котёнок":"kitten",
    "для стерилизованных":"sterilised", "стерилизованных":"sterilised",
    "стерил":"sterilised", "стерилиз":"sterilised", "sterilized":"sterilised",
    "кош.":"cat", "соб.":"dog",
    "взрослых":"adult", "взросл":"adult", "юниор":"junior",
    "пожилых":"senior", "котёнка":"kitten",
    "беззерновой":"grainfree", "беззернов":"grainfree", "grain free":"grainfree",
    "сухой":"dry", "сух":"dry", "влажный":"wet", "влаж":"wet",
    "корм":"food", "консервы":"wet", "конс":"wet", "пауч":"pouch",
    "паштет":"pate", "уринари":"urinary", "гастро":"gastro", "гепатик":"hepatic", "лайт":"light", "хэйрбол":"hairball", "полнорационный":"food", "полнорационным":"food", "лакомства":"treat", "лакомство":"treat",
    "морская рыба":"fish", "белая рыба":"fish", "сельдь":"herring", "сардина":"sardine", "курица":"chicken", "курицы":"chicken",
    "курицей":"chicken", "индейка":"turkey", "индейки":"turkey", "индейкой":"turkey",
    "утка":"duck", "утки":"duck", "кролик":"rabbit", "кролика":"rabbit",
    "лосось":"salmon", "лосося":"salmon", "лососем":"salmon",
    "говядина":"beef", "говядины":"beef", "говядиной":"beef", "ягнёнок":"lamb", "ягненок":"lamb",
    "ягнятина":"lamb", "ягненка":"lamb", "свинина":"pork",
    "рыба":"fish", "рыбы":"fish", "тунец":"tuna", "тунца":"tuna",
    "креветка":"shrimp", "креветкой":"shrimp", "креветки":"shrimp",
    "кальмар":"squid", "кальмаром":"squid",
    "макрель":"mackerel", "макрелью":"mackerel", "зайчатина":"hare",
    "оленина":"venison", "олениной":"venison",
    "страус":"ostrich", "картофель":"potato", "рисом":"rice", "рис":"rice",
    "зелёный":"green", "зеленый":"green", "зелёная":"green", "зеленая":"green", "красный":"red", "красная":"red", "красное":"red",
    "синий":"blue", "синяя":"blue", "синее":"blue", "жёлтый":"yellow", "желтый":"yellow", "желтая":"yellow",
    "чёрный":"black", "черный":"black", "черная":"black", "белый":"white",
    "розовый":"pink", "розовая":"pink", "серый":"gray", "серая":"gray", "голубой":"lightblue", "голубая":"lightblue",
    "коричневый":"brown", "оранжевый":"orange",
    "фиолетовый":"purple", "бежевый":"beige",
    "маленьких":"small", "мелких":"small", "миниатюрных":"small", "мелк":"small",
    "крупных":"large", "больших":"large", "средних":"medium", "крупн":"large", "мини":"mini", "макси":"maxi",
    "пород":"breed", "породы":"breed", "в ассортименте":"assorted",
    "в асс":"assorted", "самофиксирующийся":"self-lock",
    "мм":"mm", "см":"cm", "гр":"g", "г":"g", "кг":"kg",
    "мл":"ml", "л":"l", "шт":"pcs",
}

ALIASES.update({
    "сибау":"cibau", "джози дог":"josidog", "санал":"sanal",
    "ванпи":"wanpy", "нюво":"nuevo", "ньюво":"nuevo",
    "доктор вик":"doctor vic", "доктор виктор":"doctor vic",
    "вет лайф":"farmina vet life", "ветлайф":"farmina vet life",
    "фотоэко":"fotoeco", "форсекто":"forsecto",
    "селафорт":"selafort", "адвокат":"advocate",
    "эквилибриум":"equilibrium", "прайм натур":"prime nature",
    "мяумс":"mnyams", "карни":"carny", "кэти":"cat",
    "котики собачки":"kotiki sobachki",
    "в асс":"assorted", "пометка":"", "прочее":"",
    "микросилбержангель":"mikrosilber zahngel",
    "зубной гель":"zahngel", "зубной":"dental", "зубные":"dental",
    "спот он":"spot on", "д/животн":"animals", "животн":"animals",
    "гипоалл":"hypoallergenic", "гипоаллерген":"hypoallergenic",
    "счп":"sensitive", "чувств":"sensitive", "чувствит":"sensitive",
    "пищевар":"digestion", "желудочно":"gastro",
    "утк":"duck", "клюк":"cranberry", "морк":"carrot",
    "говяд":"beef", "ягн":"lamb", "лос":"salmon", "кур":"chicken",
    "тел":"veal", "крол":"rabbit", "черн":"blueberry",
    "цыпленок":"chicken", "цыпленком":"chicken",
    "брит премиум":"brit premium",
    "картош":"potato", "рисов":"rice",
    "в соусе":"gravy", "соус":"gravy", "с соусом":"gravy",
    "мясные кусочки":"meat pieces", "мяс кус":"meat pieces",
    "мяс":"meat", "кус":"pieces",
    "д кош":"cat", "д соб":"dog", "д кот":"cat",
    "взр":"adult", "взрос":"adult", "щенк":"puppy",
    "стерил":"sterilised", "стер":"sterilised",
    "мочевыводящих":"urinary", "мочевыводящей":"urinary",
    "мочекаменной":"urinary",
    "натурал":"natural", "суперпремиум":"superpremium",
    "комкующийся":"clumping", "силикагелевый":"silica",
    "пуппи":"puppy", "паппи":"puppy", "киттен":"kitten",
    "эдалт":"adult", "адульт":"adult",
    "зелен":"green", "сер":"gray", "роз":"pink", "голуб":"lightblue",
    "бел":"white", "красн":"red", "желт":"yellow",
    "птиц":"poultry", "птица":"poultry",
    "юн":"junior", "бэби":"baby",
    "полнорац":"food", "консервированный":"wet",
    "консерв":"wet", "kонсервы":"wet",
    "фл":"", "упак":"", "шт":"pcs",
})

PHRASE_PATTERN = re.compile("|".join(r"(?<!\w)" + re.escape(k) + r"(?!\w)"
                                     for k in sorted(ALIASES, key=len, reverse=True)))
STOP = frozenset("""для из по на с со во в к ко от а и или при под без не до перед после
the with and of in on for to new pet pets pure нежном вкусом вкус аромат
упаковка упаковке упак шт комплект арт товар товары вкл включая
""".split())
SPECIES = {"cat", "dog", "bird", "fish", "rodent", "horse"}
AGE = {"puppy", "kitten", "adult", "senior", "junior"}
FLAVORS = {"chicken","turkey","duck","rabbit","salmon","herring","sardine","beef",
           "lamb","pork","fish","tuna","shrimp","squid","mackerel","hare",
           "venison","ostrich","potato","rice"}
LINES = {"light","dental","urinary","renal","gastro","gastrointestinal","struvite",
         "hepatic","sensitive","sensible","hairball","metabolic","hypoallergenic",
         "indoor","bountiful","pacifica","prairie","sterilised","fit","veterinary",
         "hepat","hypoallergen","diabetic","weightcontrol","antihairball"}
SIZES = {"small","mini","medium","large","maxi","xs","xl","xxl","xxs"}
COLORS = {"red","blue","yellow","black","white","pink","gray","green",
          "lightblue","brown","orange","purple","beige"}
BRANDS = {
 "royal canin", "natures protection", "purina", "pro plan", "brit",
 "brit care", "hills", "josera", "chicopee", "acana", "orijen", "monge",
 "farmina", "fitmin", "bosch", "eukanuba", "alphapet", "ambrosia", "whiskas",
 "grandorf", "brooksfield", "sirius", "mnyams", "cliny", "flexi", "furminator",
 "ferplast", "derevenskie lakomstva", "little one", "bunny", "triol",
 "gamma", "sanabelle", "apicenna", "prazicid", "drontal", "bars", "rolf club",
 "zoonik", "petline", "green qzin", "molina", "imac", "collar", "harper",
 "schesir", "cibau", "flatazor", "amity", "artero", "codos", "wahl", "josi",
 "chammy", "vitakraft", "titan", "sera", "beaphar", "hill", "kippy",
 "grandorf", "go", "now", "zoo", "8in1", "8 in 1", "happy dog", "happy cat",
 "hunter", "petstages", "trixie", "carnilove", "summit", "savic", "croci", "moderna",
 "dezzie", "best dinner", "ownat", "1st choice", "one"
}
SIZE_RE = re.compile(r"(?<!\w)(\d+(?:[.,]\d+)?)\s*(кг|kg|гр|г|gr|g|мг|mg|мкг|mcg|мл|ml|л|l|см|cm|мм|mm)\b",re.I)
CODE_RE = re.compile(r"(?<!\w)([a-zа-я]{1,9})[\s_-]*(\d{3,7}[a-zа-я]?)\b", re.I)

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).lower().replace("ё","е")
    text = text.replace("'", "").replace("’", "").replace("«", " ").replace("»", " ")
    text = re.sub(r"^\s*(?:\d{4,12}[a-zа-я]{0,2})\s+", "", text)
    text = re.sub(r"1\s*\+\s*1(?:\s*=\s*3)?", " ", text)
    text = SIZE_RE.sub(" ", text)
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=\w)[./](?=\w)", " ", text)
    text = PHRASE_PATTERN.sub(lambda match: ALIASES[match.group()], text)
    text = re.sub(r"[^\w.]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())

def units(text: str) -> frozenset[tuple[str, int]]:
    found: set[tuple[str, int]] = set()
    for value, suffix in SIZE_RE.findall(unicodedata.normalize("NFKC",text.lower()).replace("ё","е")):
        numeric = float(value.replace(",", "."))
        suffix = suffix.lower()
        if suffix in ("кг","kg"): kind, number = "mass", numeric * 1000
        elif suffix in ("гр","г","gr","g"): kind, number = "mass", numeric
        elif suffix in ("мг","mg"): kind, number = "dose", numeric
        elif suffix in ("мкг","mcg"): kind, number = "dose", numeric / 1000
        elif suffix in ("л","l"): kind, number = "volume", numeric * 1000
        elif suffix in ("мл","ml"): kind, number = "volume", numeric
        elif suffix in ("см","cm"): kind, number = "length", numeric * 10
        else: kind, number = "length", numeric
        found.add((kind, round(number)))
    return frozenset(found)

def codes(text: str) -> frozenset[str]:
    raw = unicodedata.normalize("NFKC",text.lower()).replace("ё","е")
    raw = SIZE_RE.sub(" ", raw)
    return frozenset(prefix + number for prefix, number in CODE_RE.findall(raw))

def detect_brand(normalized: str) -> str:
    value = " " + normalized + " "
    for brand in sorted(BRANDS, key=lambda v: -len(v)):
        if " " + brand + " " in value:
            return brand
    return ""

@dataclass(frozen=True)
class Product:
    row: int
    name: str
    normalized: str
    tokens: frozenset[str]
    sizes: frozenset[tuple[str, int]]
    codes: frozenset[str]
    brand: str
    species: frozenset[str]
    ages: frozenset[str]
    flavors: frozenset[str]
    colors: frozenset[str]
    variants: frozenset[str]
    lines: frozenset[str]
    url: str = ""
    sku: str = ""
    product_url: str = ""

def build_product(row: int, name: str, url: str = "", sku: str = "",
                  product_url: str = "", category: str = "") -> Product:
    normalized = normalize(name)
    tokens = frozenset(w for w in normalized.split() if w not in STOP and len(w)>1)
    category_normalized = normalize(category).split()
    known_species = (set(tokens) | set(category_normalized)) & SPECIES
    variants=set(tokens & SIZES)
    short=re.search(r"puppy\s*(?:&|and)\s*junior\s+(s|m|l|xl)\b",name.lower())
    if short: variants.add({"s":"small","m":"medium","l":"large","xl":"xl"}[short.group(1)])
    return Product(row, name.strip(), normalized, tokens, units(name), codes(name),
                   detect_brand(normalized), frozenset(known_species),
                   frozenset(tokens & AGE), frozenset(tokens & FLAVORS),
                   frozenset(tokens & COLORS), frozenset(variants),
                   frozenset(tokens & LINES), url.strip(), sku.strip(), product_url.strip())

@dataclass(frozen=True)
class Match:
    product: Product | None
    score: float
    status: str
    reason: str
    alternatives: tuple[tuple[float, Product], ...] = ()

class Matcher:
    def __init__(self, catalog: list[Product]) -> None:
        self.catalog = [p for p in catalog if p.name and p.url and
                        urlparse(p.url).scheme in ("http", "https") and urlparse(p.url).netloc]
        self.postings: dict[str,list[int]] = defaultdict(list)
        self.exact: dict[str,list[int]] = defaultdict(list)
        self.skus: dict[str,list[int]] = defaultdict(list)
        self.model_codes: dict[str,list[int]] = defaultdict(list)
        for index, product in enumerate(self.catalog):
            self.exact[product.normalized].append(index)
            if product.sku:
                self.skus[re.sub(r"\W","",product.sku.lower())].append(index)
            for code in product.codes:
                self.model_codes[code].append(index)
            for word in product.tokens:
                self.postings[word].append(index)
        total = len(self.catalog)
        self.idf = {word: max(.3, min(5.0, log(1 + total / len(ids))))
                    for word,ids in self.postings.items()}

    def _conflicts(self, source: Product, target: Product) -> tuple[list[str],list[str]]:
        hard: list[str] = identity_conflicts(source.normalized,target.normalized,source.name)
        soft: list[str] = []
        if source.brand and target.brand and source.brand != target.brand:
            hard.append("другая марка")
        if source.species and target.species and not source.species.intersection(target.species):
            hard.append("другое животное")
        if source.ages and target.ages and not source.ages.intersection(target.ages):
            # junior/puppy могут обозначать один и тот же жизненный этап
            if not (source.ages | target.ages) <= {"junior","puppy","kitten"}:
                hard.append("другой возраст")
        if source.flavors and target.flavors and not source.flavors.intersection(target.flavors):
            hard.append("другой вкус")
        if source.colors and target.colors and not source.colors.intersection(target.colors):
            hard.append("другой цвет")
        if source.lines and target.lines and not source.lines.intersection(target.lines):
            hard.append("другая линейка/назначение")
        if source.variants and target.variants:
            clusters={"small":"small","mini":"small","medium":"medium","large":"large","maxi":"large",
                      "xs":"xs","xl":"xl","xxs":"xxs","xxl":"xxl"}
            left={clusters[x] for x in source.variants}
            right={clusters[x] for x in target.variants}
            if not left.intersection(right):
                hard.append("другой размерный класс")
        for family in ("mass","dose","volume","length"):
            left={v for unit,v in source.sizes if unit==family}
            right={v for unit,v in target.sizes if unit==family}
            if left and right and not any(abs(a-b) <= (5 if family=="length" else 0) for a in left for b in right):
                hard.append("другая фасовка/размер")
            elif left and not right:
                soft.append("размер отсутствует в каталоге")
        if source.codes and target.codes and not source.codes.intersection(target.codes):
            hard.append("другая модель")
        return hard,soft

    def _score(self, source: Product, candidate: Product) -> tuple[float,str]:
        hard,soft=self._conflicts(source,candidate)
        if hard:
            return -1.0, ", ".join(hard)
        if source.normalized == candidate.normalized:
            return 1.0,"точное название"
        shared=source.tokens & candidate.tokens
        if not shared:
            return 0.0,"нет общих слов"
        left=sum(self.idf.get(t,2.0) for t in sorted(source.tokens))
        right=sum(self.idf.get(t,2.0) for t in sorted(candidate.tokens))
        common=sum(self.idf.get(t,2.0) for t in sorted(shared))
        coverage= .60*(common/max(left,.01)) + .40*(common/max(right,.01))
        ratio=SequenceMatcher(None,source.normalized,candidate.normalized,autojunk=False).ratio()
        score=.72*coverage+.28*ratio
        if source.brand and candidate.brand and source.brand==candidate.brand:
            score+=.075
        if source.codes and candidate.codes and source.codes.intersection(candidate.codes):
            score+=.20
        if source.sizes and candidate.sizes and source.sizes.intersection(candidate.sizes):
            score+=.06
        if source.flavors and candidate.flavors and source.flavors.intersection(candidate.flavors):
            score+=.03
        if source.species and candidate.species and source.species.intersection(candidate.species):
            score+=.02
        if source.ages and candidate.ages and source.ages.intersection(candidate.ages):
            score+=.02
        if soft: score-=.055
        if source.brand and not candidate.brand: score-=.035
        if source.flavors and not candidate.flavors: score-=.045
        if source.colors and not candidate.colors: score-=.06
        if source.lines and not candidate.lines: score-=.07
        if candidate.lines and not source.lines: score-=.07
        return min(1.0,max(0.0,score)), ", ".join(soft) or "совпадают основные признаки"

    def match(self, source: Product, candidate_limit: int = 110) -> Match:
        if not source.tokens:
            return Match(None,0.0,"Пропущено","нет названия")
        candidates: Counter[int] = Counter()
        for index in self.exact.get(source.normalized,[]):
            candidates[index]+=100
        for code in sorted(source.codes):
            for index in self.model_codes.get(code,[]):
                candidates[index]+=25
            for index in self.skus.get(re.sub(r"\W","",code.lower()),[]):
                candidates[index]+=50
        for word in sorted(source.tokens):
            frequency=self.idf.get(word,2.0)
            if frequency < .5: continue
            for index in self.postings.get(word,[]):
                candidates[index]+=frequency
        if not candidates:
            return Match(None,0.0,"Нет совпадения","в каталогах нет подходящих названий")
        shortlisted=[index for index,_ in sorted(candidates.items(),
                                           key=lambda kv: (-kv[1],kv[0]))[:candidate_limit]]
        scored: list[tuple[float,Product,str]] = []
        for index in shortlisted:
            candidate=self.catalog[index]
            score,why=self._score(source,candidate)
            if score>0: scored.append((score,candidate,why))
        if not scored:
            return Match(None,0.0,"Нет совпадения","исключены товары с конфликтующими признаками")
        scored.sort(key=lambda x:(-x[0],x[1].name,x[1].url))
        best_score,best,why=scored[0]
        alternatives=tuple((score,c) for score,c,_ in scored[:5])
        # Несколько одинаковых карточек товара не должны искусственно создавать неоднозначность.
        second_distinct=next(((s,c) for s,c,_ in scored[1:] if c.url!=best.url),None)
        gap=best_score-second_distinct[0] if second_distinct else 1.0
        if best_score>=.85 and gap>=.065 and not ("размер отсутствует" in why):
            status="Надёжно"
        elif best_score>=.73 and gap>=.045:
            status="Вероятно"
        elif best_score>=.60:
            status="Проверить"
        else:
            return Match(None,best_score,"Нет совпадения",
                         f"недостаточно сходства, лучший вариант {best_score:.2f}", alternatives)
        if gap<.035 and second_distinct and best_score<.98:
            status="Проверить"
            why += ", есть похожие альтернативы"
        # Даже спорный результат заполнен, но отдельная колонка явно предупреждает о риске.
        return Match(best,best_score,status,why,alternatives)
