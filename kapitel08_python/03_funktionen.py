"""Kapitel 8: Funktionen, Typ-Hinweise, Standard- und Schlüsselwortargumente."""
from typing import Optional


def als_zahl(state: str, standard: Optional[float] = None) -> Optional[float]:
    """Wandelt einen openHAB-Zustand wie '21.5 °C' in eine Zahl um."""
    if state in ("NULL", "UNDEF"):
        return standard
    try:
        return float(state.split(" ")[0])
    except ValueError:
        return standard


def mittelwert(*werte: float) -> float:
    """Beliebig viele Positionsargumente landen im Tupel "werte"."""
    return sum(werte) / len(werte) if werte else 0.0


def item_json(name: str, typ: str, *, label: str = "", **extra) -> dict:
    """Nach * nur noch Schlüsselwortargumente; **extra sammelt den Rest."""
    return {"name": name, "type": typ, "label": label, **extra}


print(als_zahl("21.5 °C"), als_zahl("NULL", standard=0.0))
print(mittelwert(20.5, 21.0, 22.5))
print(item_json("Garten_Pumpe", "Switch", label="Pumpe", category="water"))

# Funktionen sind Objekte – man kann sie übergeben (Rückruffunktionen)
def bei_aenderung(name: str, alt: str, neu: str) -> None:
    print(f"{name}: {alt} -> {neu}")

beobachter = [bei_aenderung, lambda n, a, z: print("Lambda sieht", n)]
for rueckruf in beobachter:
    rueckruf("Wohnzimmer_Licht", "OFF", "ON")
