"""
Kapitel 20: openHAB als Werkzeugkasten für ein Sprachmodell (Function Calling).

Moderne Sprachmodelle können »Werkzeuge« aufrufen: Die Anwendung beschreibt
Funktionen mit Name, Zweck und JSON-Schema; das Modell antwortet nicht mit
Text, sondern mit dem Wunsch »rufe send_command mit {...} auf«. Die
Anwendung führt den Aufruf aus und gibt das Ergebnis zurück.

Dieses Modul ist bewusst anbieterneutral: WERKZEUGE lässt sich in das
Werkzeugformat jeder gängigen LLM-API übertragen, fuehre_aus() ist der
Teil, der mit openHAB spricht. Sicherheit steht dabei an erster Stelle:
Ein Modell darf nur Items bedienen, die ausdrücklich freigegeben sind.
"""

from __future__ import annotations

import json
import os

from openhab import OpenHABClient, Items

FREIGEGEBEN = {
    "Wohnzimmer_Licht",
    "Wohnzimmer_Dimmer",
    "Kueche_Rollladen",
    "Wohnzimmer_Temperatur",
    "Flur_Haustuer",
    "Werkstatt_Luefter",
}
NUR_LESEN = {"Wohnzimmer_Temperatur", "Flur_Haustuer"}

WERKZEUGE = [
    {
        "name": "list_devices",
        "description": "Listet die freigegebenen Geräte mit Typ und Zustand.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_state",
        "description": "Liest den aktuellen Zustand eines Geräts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item": {
                    "type": "string",
                    "description": "Itemname, z. B. Wohnzimmer_Licht",
                }
            },
            "required": ["item"],
        },
    },
    {
        "name": "send_command",
        "description": "Sendet einen Befehl (ON/OFF, 0-100, UP/DOWN/STOP).",
        "input_schema": {
            "type": "object",
            "properties": {
                "item": {"type": "string"},
                "command": {"type": "string"},
            },
            "required": ["item", "command"],
        },
    },
]


class OpenHABWerkzeuge:
    def __init__(self, items: Items):
        self.items = items

    def fuehre_aus(self, name: str, argumente: dict) -> str:
        """Führt einen Werkzeugaufruf aus; Ergebnis als JSON-Text."""
        try:
            ergebnis = getattr(self, f"_{name}")(**argumente)
        except AttributeError:
            ergebnis = {"error": f"unbekanntes Werkzeug {name}"}
        except TypeError as fehler:
            ergebnis = {"error": f"falsche Argumente: {fehler}"}
        return json.dumps(ergebnis, ensure_ascii=False)

    def _list_devices(self):
        return [
            {
                "item": i["name"],
                "label": i["label"],
                "type": i["type"],
                "state": i["state"],
                "steuerbar": i["name"] not in NUR_LESEN,
            }
            for i in self.items.getItems(fields="name,label,type,state")
            if i["name"] in FREIGEGEBEN
        ]

    def _get_state(self, item: str):
        if item not in FREIGEGEBEN:
            return {"error": f"{item} ist nicht freigegeben"}
        return {"item": item, "state": self.items.getItemState(item)}

    def _send_command(self, item: str, command: str):
        if item not in FREIGEGEBEN or item in NUR_LESEN:
            return {"error": f"{item} darf nicht gesteuert werden"}
        return {
            "item": item,
            "command": command,
            **self.items.sendCommand(item, command),
        }


if __name__ == "__main__":
    # Demonstration ohne Sprachmodell: so sähen die Werkzeugaufrufe aus,
    # die ein Modell auf »Mach es im Wohnzimmer gemütlich« erzeugen könnte.
    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    werkzeuge = OpenHABWerkzeuge(Items(client))
    for aufruf in [
        ("list_devices", {}),
        ("send_command", {"item": "Wohnzimmer_Dimmer", "command": "30"}),
        ("send_command", {"item": "Kueche_Rollladen", "command": "DOWN"}),
        ("send_command", {"item": "Flur_Haustuer", "command": "OPEN"}),
        ("get_state", {"item": "Wohnzimmer_Dimmer"}),
    ]:
        print(
            f"{aufruf[0]}({aufruf[1]})\n  -> {werkzeuge.fuehre_aus(*aufruf)[:150]}"
        )
