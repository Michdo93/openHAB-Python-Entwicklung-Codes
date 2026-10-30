"""Controller: übersetzt Benutzeraktionen in Commands (State-Command-Pattern)."""

from __future__ import annotations

import logging

from openhab import Items

from .model import ItemModel

log = logging.getLogger(__name__)


class Controller:
    def __init__(self, items: Items, model: ItemModel):
        self.items = items
        self.model = model

    def umschalten(self, name: str) -> None:
        """Schalter umlegen – der neue Zustand kommt über den Ereignisstrom."""
        neu = "OFF" if self.model[name].state == "ON" else "ON"
        self.senden(name, neu)

    def senden(self, name: str, command: str) -> None:
        antwort = self.items.sendCommand(name, command)
        if isinstance(antwort, dict) and "error" in antwort:
            log.error(
                "Command %s an %s abgelehnt: %s", command, name, antwort["error"]
            )
        # Bewusst KEIN self.model.setze_zustand(...):
        # openHAB ist die Quelle der Wahrheit (State-Command-Pattern).
