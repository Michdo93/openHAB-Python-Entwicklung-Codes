"""View 1: Ausgabe auf der Konsole."""
from __future__ import annotations

from datetime import datetime

from .model import Item, ItemModel


class ConsoleView:
    def __init__(self, model: ItemModel):
        model.anmelden(self)
        self.model = model

    def tabelle(self) -> None:
        for item in self.model:
            print(f"  {item.label:<20} {item.state}")

    def item_geaendert(self, item: Item, alt: str) -> None:
        zeit = datetime.now().strftime("%H:%M:%S")
        print(f"[{zeit}] {item.label:<20} {alt:>10} -> {item.state}")
