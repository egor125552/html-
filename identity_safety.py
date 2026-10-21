"""Независимая проверка идентичности модели и названия препарата."""
from __future__ import annotations
import re

# Важные названия препаратов не допускают замены на "похожее средство".
DRUG_NAMES = frozenset({
    "ципровет","апоквел","бравекто","нобивак","милпразон",
    "холликалм","энроксил","форсекто","forsecto","селафорт","selafort",
    "празицид","prazicid","дирофен","гепатовет","кладакса",
    "риванол","празител","милбемакс","фронтлайн","симпарика",
    "габа","превикокс","каниквантел",
})

def terms(text: str) -> set[str]:
    return set(re.findall(r"[\w]+",text.lower().replace("ё","е")))

def conflicts(source: str, target: str, raw_source: str = "") -> list[str]:
    src=terms(source)
    dst=terms(target)
    found=[]
    missing=sorted(name for name in DRUG_NAMES if name in src and name not in dst)
    if missing:
        found.append("другое торговое название препарата: " + ", ".join(missing))
    toy_shapes={"огурчик","осьминожка","осьминог","скат","улитка",
                "кактус","лобстер","питахайя","walrus","octopus"}
    a=src & toy_shapes
    b=dst & toy_shapes
    if a and b and not a.intersection(b):
        found.append("другая форма или персонаж игрушки")
    bowl_series={"candy","diamond","daimond"}
    a=src & bowl_series
    b=dst & bowl_series
    if a and b and not a.intersection(b):
        found.append("другая серия посуды")
    if "frosty" in src and "frosty" not in dst:
        found.append("другая линейка: фросты")
    if "палочки" in src and ("крем" in dst or "консервы" in dst):
        found.append("другая форма лакомства")
    if "соломка" in src and "сублимированное" in dst and "соломка" not in dst:
        found.append("другая форма лакомства")
    if "нарезка" in src and "косичка" in dst or "косичка" in src and "нарезка" in dst:
        found.append("другая форма лакомства")
    if ("sport" in src or "спорт" in src) and ("standard" in dst or "стандарт" in dst):
        found.append("другая модель Sport/Standard")
    if ("standard" in src or "стандарт" in src) and ("sport" in dst or "спорт" in dst):
        found.append("другая модель Standard/Sport")
    if ("mini" in dst or "small" in dst) and not ({"mini","small"}&src):
        if re.search(r"\bот\s+(?:11|12|13|14|15)\s*(?:кг|kg)\b",raw_source.lower()):
            found.append("корм Mini не для заявленной весовой категории собак")
    return found
