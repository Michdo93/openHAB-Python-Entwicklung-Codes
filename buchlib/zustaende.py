"""
Hilfsfunktionen für openHAB-Zustände.

openHAB liefert jeden Zustand als Zeichenkette – auch Zahlen, oft mit
Einheit (»21.5 °C«), und jederzeit möglicherweise als NULL oder UNDEF.
Diese Funktionen wandeln Zustände sicher in Python-Werte um.
"""

from __future__ import annotations

from dataclasses import dataclass

UNBEKANNT = ("NULL", "UNDEF")


def ist_bekannt(state: str | None) -> bool:
    """True, wenn der Zustand ein echter Wert ist (nicht NULL/UNDEF/None)."""
    return state is not None and state not in UNBEKANNT


def als_zahl(state: str | None, standard: float | None = None) -> float | None:
    """'21.5 °C' -> 21.5; 'NULL' -> standard."""
    if not ist_bekannt(state):
        return standard
    try:
        return float(state.split(" ")[0])
    except (ValueError, AttributeError):
        return standard


def einheit(state: str | None) -> str:
    """'21.5 °C' -> '°C'; '42' -> ''."""
    if not ist_bekannt(state) or " " not in state:
        return ""
    return state.split(" ", 1)[1]


def als_bool(state: str | None) -> bool | None:
    """ON/OPEN/>0 -> True, OFF/CLOSED/0 -> False, sonst None."""
    if not ist_bekannt(state):
        return None
    if state in ("ON", "OPEN"):
        return True
    if state in ("OFF", "CLOSED"):
        return False
    zahl = als_zahl(state)
    return None if zahl is None else zahl > 0


@dataclass(frozen=True)
class HSB:
    """Farbe im HSB-Format von openHAB ('240,100,75')."""

    farbton: float
    saettigung: float
    helligkeit: float

    @classmethod
    def aus_state(cls, state: str) -> "HSB":
        h, s, b = (float(x) for x in state.split(","))
        return cls(h, s, b)

    def als_command(self) -> str:
        return f"{self.farbton:g},{self.saettigung:g},{self.helligkeit:g}"
