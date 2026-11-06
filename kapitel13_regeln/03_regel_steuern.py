"""Kapitel 13: Eine Regel ändern, abschalten, sofort ausführen und löschen."""
import os
import time

from openhab import OpenHABClient, Items, Rules

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, rules = Items(client), Rules(client)
UID = "buch_kinoabend"                 # aus 02_regel_anlegen.py

if "error" in rules.getRule(UID):
    raise SystemExit("Bitte zuerst 02_regel_anlegen.py ausführen.")


def status() -> str:
    s = rules.getRule(UID)["status"]
    return f"{s['status']} / {s['statusDetail']}"


# 1. Einen einzelnen Parameter eines Moduls ändern: Dimmer auf 10 statt 20 %
rules.setModuleConfigParam(UID, "actions", "4", "command", "10")
print("Dimmwert jetzt:", rules.getModuleConfigParam(UID, "actions", "4", "command"))

# 2. Sofort ausführen – runNow überspringt Trigger UND Bedingungen
items.sendCommand("Wohnzimmer_Dimmer", "80")
items.postUpdate("Flur_Haustuer", "OPEN")
rules.runNow(UID)
time.sleep(1)
print("runNow trotz offener Tür:", items.getItemState("Wohnzimmer_Dimmer"))

# 3. Abschalten: der Trigger wird ignoriert
rules.disable(UID)
print("abgeschaltet:", status())
items.postUpdate("Flur_Haustuer", "CLOSED")
items.sendCommand("Wohnzimmer_Dimmer", "80")
items.sendCommand("Haus_Status", "Kino")
time.sleep(1)
print("Trigger bei abgeschalteter Regel:", items.getItemState("Wohnzimmer_Dimmer"))
rules.enable(UID)
print("eingeschaltet:", status())

# 4. Die ganze Regel ersetzen: eine zusätzliche Aktion
regel = rules.getRule(UID)
regel["actions"].append({"id": "6", "type": "core.ItemStateUpdateAction",
                         "configuration": {"itemName": "Haus_Status",
                                           "state": "Film läuft"}})
rules.updateRule(UID, regel)
items.sendCommand("Haus_Status", "Kino")
time.sleep(1)
print("nach updateRule:", items.getItemState("Haus_Status"))

print("löschen:", rules.deleteRule(UID))
