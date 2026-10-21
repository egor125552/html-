"""Точечный поиск по редким идентификаторам товарной серии.

Не использует лишь общие слова («корм», «кошка», «палочки») как доказательство.
"""
from __future__ import annotations

from collections import Counter
from matching_engine import Match, Matcher, Product
from rescue_matching import GENERIC

NOISE = GENERIC | frozenset({
    "полноценный","полнорационный","дополнительный","диетический",
    "свинок","морских","кроликов","грызунов","взрослых",
    "взрослые","д","мягкий","сухой","влажный","цвет",
    "гранулы","филе","большой","маленький","ароматом",
})
SERIES_ANCHOR_MAX_FREQUENCY = 120

def _candidate_anchors(matcher: Matcher, source: Product) -> list[str]:
    result=[]
    for token in source.normalized.split()[:9]:
        n=len(matcher.postings.get(token,()))
        if token in NOISE or len(token)<4 or n<1 or n>SERIES_ANCHOR_MAX_FREQUENCY:
            continue
        if token not in result:
            result.append(token)
        if len(result)>=4:
            break
    return result

def anchor_match(matcher: Matcher, source: Product) -> Match | None:
    anchors=_candidate_anchors(matcher,source)
    if not source.brand and len(anchors)==2:
        # Two ordinary Russian descriptors or a colour do not identify a
        # manufacturer/model reliably.
        if all(not w.isascii() for w in anchors) or (set(anchors) & source.colors):
            return None
    matches=[]
    if len(anchors)>=2:
        # All recorded rare early-series words must appear in the target.
        ids=set(matcher.postings[anchors[0]])
        for word in anchors[1:]:
            ids.intersection_update(matcher.postings[word])
        for index in ids:
            candidate=matcher.catalog[index]
            if matcher._conflicts(source,candidate)[0]:
                continue
            if source.brand and source.brand != candidate.brand:
                continue
            if "snack" in candidate.tokens and not ({"snack","treat"} & source.tokens):
                continue
            if "wet" in candidate.tokens and "wet" not in source.tokens:
                continue
            if "pouch" in source.tokens and not ({"pouch","wet"} & candidate.tokens):
                continue
            if "pate" in source.tokens and "pate" not in candidate.tokens:
                continue
            # Product names like "Walrus" and "Octopus" are model identifiers.
            # If the source names an uncommon English model absent from the
            # catalog altogether, we cannot silently replace it.
            omitted={
                word for word in source.normalized.split()[:10]
                if len(word)>=5 and word.isascii() and word.isalpha()
                and word not in NOISE and word not in candidate.tokens
                and not matcher.postings.get(word)
            }
            if omitted:
                continue
            if source.ages and not source.ages.issubset(candidate.ages):
                continue
            if source.variants and candidate.variants and not source.variants.intersection(candidate.variants):
                continue
            if source.flavors and not source.flavors.issubset(candidate.flavors):
                continue
            if source.colors and not source.colors.issubset(candidate.colors):
                continue
            if source.lines and not source.lines.issubset(candidate.lines):
                continue
            matches.append(candidate)
    elif len(anchors)==1 and source.sizes:
        # One rare drug name is only useful when the exact *dose* is also present.
        dose={value for kind,value in source.sizes if kind=="dose"}
        if dose:
            for index in matcher.postings[anchors[0]]:
                candidate=matcher.catalog[index]
                target_dose={value for kind,value in candidate.sizes if kind=="dose"}
                if dose==target_dose and not matcher._conflicts(source,candidate)[0]:
                    matches.append(candidate)
    if not matches:
        return None
    urls={p.url for p in matches}
    if len(urls)>1:
        return None
    best=sorted(matches,key=lambda p:(p.name,p.row))[0]
    if not best.url.startswith("https://"):
        return None
    if len(anchors)>=2:
        weight=sum(1/max(1,len(matcher.postings[token])) for token in anchors)
        # A unique pairing is much stronger evidence than multiple generic words.
        if weight<.018:
            return None
        reason="совпала редкая товарная серия: " + ", ".join(anchors)
    else:
        reason="совпало точное название препарата и его дозировка"
    return Match(best,.62,"Проверить",
                 "Поиск по названию: " + reason +
                 ". ВНИМАНИЕ: упаковка, цвет и фотография требуют проверки",
                 ())
