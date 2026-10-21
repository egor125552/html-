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
