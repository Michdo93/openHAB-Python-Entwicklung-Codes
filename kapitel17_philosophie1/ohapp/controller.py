"""Controller: übersetzt Benutzeraktionen in REST-Aufrufe (State-Command-Pattern)."""

from __future__ import annotations

import logging

from openhab import Items, Rules

from .model import ItemModel

log = logging.getLogger(__name__)


class Controller:
    def __init__(self, items: Items, rules: Rules, model: ItemModel):
        self.items, self.rules, self.model = items, rules, model

    def umschalten(self, name: str) -> None:
        """Schalter umlegen – der neue Zustand kommt über den Ereignisstrom."""
        neu = "OFF" if self.model[name].state == "ON" else "ON"
        self.senden(name, neu)

    def senden(self, name: str, command: str) -> None:
        antwort = self.items.sendCommand(name, command, source="ohapp")
        if "error" in antwort:
            log.error("Command %s an %s abgelehnt: %s", command, name, antwort["error"])
        # Bewusst KEIN self.model.setze_zustand(...):
        # openHAB ist die Quelle der Wahrheit (State-Command-Pattern).

    def szene(self, regel_uid: str) -> None:
        """Eine vorhandene openHAB-Regel auslösen, statt ihre Logik nachzubauen."""
        antwort = self.rules.runNow(regel_uid)
        if "error" in antwort:
            log.error("Regel %s: %s", regel_uid, antwort["error"])
