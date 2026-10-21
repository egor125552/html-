"""Дополнительный подбор: только после основного поиска и с отдельной проверкой."""
from __future__ import annotations
from dataclasses import dataclass
from matching_engine import Match, Matcher, Product

GENERIC = {
    "cat", "dog", "food", "wet", "dry", "breed", "adult", "small", "mini",
    "large", "medium", "junior", "puppy", "kitten", "treat", "pcs", "pouch",
    "pate", "для", "с", "уп", "ассортименте", "корм", "животных",
    "щенка", "собак", "кошек", "лакомство", "набор", "игрушка",
    "препарат", "спрей", "шампунь", "гель", "таблетки", "средство",
    "паста", "флакон", "упаковка", "консервы", "палочки", "соус",
}

@dataclass(frozen=True)
class Evidence:
    accepted: bool
    reason: str

def evidence_for(matcher: Matcher, source: Product, target: Product) -> Evidence:
    hard,soft=matcher._conflicts(source,target)
    if hard:
        return Evidence(False, "конфликт: " + ", ".join(hard))
    common=source.tokens & target.tokens
    useful={word for word in common if word not in GENERIC}
    weighted=sum(matcher.idf.get(w,1.0) for w in useful)
    catalog_weight=sum(matcher.idf.get(w,2.0) for w in target.tokens)
    source_weight=sum(matcher.idf.get(w,2.0) for w in source.tokens)
    matched=sum(matcher.idf.get(w,2.0) for w in common)
    rare={w for w in useful if matcher.idf.get(w,2)<3.25}
    # Despite the name, weak words are not evidence on their own.
    distinctive=[w for w in useful if matcher.idf.get(w,2)>=3.25]
    brand_agreement=bool(source.brand and target.brand and source.brand==target.brand)
    model_agreement=bool(source.codes and target.codes and source.codes.intersection(target.codes))
    if len(distinctive)<2 and not model_agreement:
        return Evidence(False,"недостаточно характерных слов")
    if weighted<6.8 and not model_agreement:
        return Evidence(False,"недостаточно общих деталей")
    if matched/max(catalog_weight,1)<.53 or matched/max(source_weight,1)<.22:
        return Evidence(False,"неполное совпадение ключевых деталей")
    if not (brand_agreement or model_agreement or len(distinctive)>=3):
        return Evidence(False,"марка или модель не подтверждены")
    # If neither side provides weight or flavour, we can only put this in review.
    if source.flavors and target.flavors and len(source.flavors&target.flavors)==0:
        return Evidence(False,"состав противоречит")
    return Evidence(True, "подтверждены " + ", ".join(sorted(distinctive)[:6]))

def rescue(matcher: Matcher, source: Product, preliminary: Match) -> Match:
    if preliminary.status!="Нет совпадения" or not preliminary.alternatives:
        return preliminary
    ranking=list(preliminary.alternatives)
    best_score,best=ranking[0]
    if best_score <.43:
        return preliminary
    proof=evidence_for(matcher,source,best)
    if not proof.accepted:
        return preliminary
    competing=[(score,product) for score,product in ranking[1:] if product.url != best.url]
    # No new match if similarly plausible, differently photographed products exist.
    second=max((score for score,_ in competing),default=0)
    gap=best_score-second
    if gap<.065:
        return preliminary
    return Match(best,round(best_score,4),"Проверить",
                 "Дополнительный поиск: " + proof.reason + ". Фасовку и изображение проверить",
                 preliminary.alternatives)
