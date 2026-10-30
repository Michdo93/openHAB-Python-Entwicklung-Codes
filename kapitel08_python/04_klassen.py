"""Kapitel 8: Klassen, Vererbung und Dataclasses."""
from dataclasses import dataclass, field


class Geraet:
    """Basisklasse für ein schaltbares Gerät."""

    def __init__(self, name: str, label: str):
        self.name = name
        self.label = label
        self._state = "NULL"            # _ = »intern, bitte nicht von außen«

    @property
    def state(self) -> str:
        return self._state

    def melde(self, state: str) -> None:
        self._state = state

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, state={self._state!r})"


class Lampe(Geraet):
    """Eine Lampe ist ein Gerät mit zusätzlicher Methode."""

    def ist_an(self) -> bool:
        return self.state == "ON"


@dataclass
class ItemInfo:
    """Dataclass: __init__, __repr__ und Vergleich werden erzeugt."""
    name: str
    type: str
    state: str = "NULL"
    tags: list[str] = field(default_factory=list)


lampe = Lampe("Wohnzimmer_Licht", "Deckenlicht")
lampe.melde("ON")
print(lampe, lampe.ist_an(), isinstance(lampe, Geraet))

info = ItemInfo("Wohnzimmer_Temperatur", "Number:Temperature", "21.5 °C")
print(info, info == ItemInfo("Wohnzimmer_Temperatur", "Number:Temperature",
                             "21.5 °C"))
