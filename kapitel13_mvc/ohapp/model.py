"""Model: hält die Item-Zustände und benachrichtigt Beobachter (Observer)."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass
class Item:
    name: str
    type: str
    label: str
    state: str = "NULL"


class ItemBeobachter(Protocol):
    """Schnittstelle, die jede View erfüllen muss."""

    def item_geaendert(self, item: Item, alt: str) -> None: ...


class ItemModel:
    """Subject im Observer-Pattern – kennt weder openHAB noch Bildschirme."""

    def __init__(self, namen: Iterable[str] | None = None):
        self._filter = set(namen) if namen else None
        self._items: dict[str, Item] = {}
        self._beobachter: list[ItemBeobachter] = []
        self._lock = threading.Lock()

    # --- Observer-Verwaltung ------------------------------------------------
    def anmelden(self, beobachter: ItemBeobachter) -> None:
        self._beobachter.append(beobachter)

    def _benachrichtigen(self, item: Item, alt: str) -> None:
        for b in list(self._beobachter):
            b.item_geaendert(item, alt)

    # --- Daten ----------------------------------------------------------------
    def laden(self, daten: Iterable[dict]) -> None:
        """Momentaufnahme übernehmen (Liste von Item-Dictionaries)."""
        for d in daten:
            if self._filter and d["name"] not in self._filter:
                continue
            self.setze_zustand(
                d["name"],
                d.get("state", "NULL"),
                typ=d.get("type", ""),
                label=d.get("label", d["name"]),
            )

    def setze_zustand(
        self, name: str, state: str, typ: str = "", label: str = ""
    ) -> None:
        """Einziger Weg, auf dem sich ein Zustand ändert."""
        if self._filter and name not in self._filter:
            return
        with self._lock:
            item = self._items.get(name)
            if item is None:
                item = self._items[name] = Item(name, typ, label or name)
            alt, item.state = item.state, state
        if alt != state:
            self._benachrichtigen(item, alt)

    def __getitem__(self, name: str) -> Item:
        return self._items[name]

    def __iter__(self):
        return iter(sorted(self._items.values(), key=lambda i: i.name))
