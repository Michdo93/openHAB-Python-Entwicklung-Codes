"""Kapitel 13: Eine Regel per REST anlegen – ganz ohne Skriptsprache."""
import os
import time

from openhab import OpenHABClient, Items, Rules

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, rules = Items(client), Rules(client)
UID = "buch_kinoabend"


def befehl(modul_id: str, item: str, command: str) -> dict:
    """Ein Aktionsmodul: 'sende Command an Item'."""
    return {"id": modul_id, "type": "core.ItemCommandAction",
            "configuration": {"itemName": item, "command": command}}


regel = {
    "uid": UID,
    "name": "Kinoabend",
    "description": "Licht dimmen und Rollladen schließen, wenn die Haustür zu ist.",
    "tags": ["Buch", "Szene"],
    "triggers": [{"id": "1", "type": "core.ItemCommandTrigger",
                  "configuration": {"itemName": "Haus_Status", "command": "Kino"}}],
    "conditions": [{"id": "2", "type": "core.ItemStateCondition",
                    "configuration": {"itemName": "Flur_Haustuer", "operator": "=",
                                      "state": "CLOSED"}}],
    "actions": [befehl("3", "Wohnzimmer_Licht", "OFF"),
                befehl("4", "Wohnzimmer_Dimmer", "20"),
                befehl("5", "Kueche_Rollladen", "DOWN")],
}

rules.deleteRule(UID)                         # falls vom letzten Lauf noch vorhanden
print("anlegen:", rules.createRule(regel))
print("Status: ", rules.getRule(UID)["status"]["status"])


def zustand() -> str:
    return ", ".join(f"{n}={items.getItemState(n)}" for n in
                     ("Wohnzimmer_Licht", "Wohnzimmer_Dimmer", "Kueche_Rollladen"))


# Ausgangslage herstellen
for name, cmd in (("Wohnzimmer_Licht", "ON"), ("Wohnzimmer_Dimmer", "80"),
                  ("Kueche_Rollladen", "UP")):
    items.sendCommand(name, cmd)

# 1. Tür offen: die Bedingung verhindert die Aktionen
items.postUpdate("Flur_Haustuer", "OPEN")
items.sendCommand("Haus_Status", "Kino")
time.sleep(1)
print("Tür offen: ", zustand())

# 2. Tür zu: die Regel greift
items.postUpdate("Flur_Haustuer", "CLOSED")
items.sendCommand("Haus_Status", "Kino")
time.sleep(1)
print("Tür zu:    ", zustand())
