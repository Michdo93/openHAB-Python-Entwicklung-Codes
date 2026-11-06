"""Kapitel 11: Gruppen zur Laufzeit ändern und den Zustandsverlauf eines Items lesen."""
import os
import time
from datetime import datetime

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)

# Ein per REST angelegtes Licht in die Gruppe aller Lichter aufnehmen
items.addOrUpdateItem("Flur_Licht", {"type": "Switch", "name": "Flur_Licht",
                                     "label": "Flurlicht", "tags": ["Switch", "Light"]})
print("aufnehmen:", items.addGroupMember("gLichter", "Flur_Licht"))
print("Mitglieder:", [m["name"] for m in items.getItem("gLichter")["members"]])

# Ein Command an die Gruppe erreicht alle Mitglieder
items.sendCommand("gLichter", "OFF")
items.sendCommand("Flur_Licht", "ON")
time.sleep(0.3)
print("gLichter:", items.getItemState("gLichter"), "(mindestens eines ist an)")

# openHAB 5 merkt sich den vorherigen Zustand und die Zeitpunkte
licht = items.getItem("Flur_Licht")
zeit = lambda ms: datetime.fromtimestamp(ms / 1000).strftime("%H:%M:%S")
print(f"Flur_Licht: {licht['state']} (vorher {licht['lastState']}), "
      f"aktualisiert {zeit(licht['lastStateUpdate'])}, "
      f"geändert {zeit(licht['lastStateChange'])}")

# In welchen Gruppen steckt das Item – bis ganz nach oben? (parents=True)
def kette(item: dict) -> list:
    return [[p["name"]] + k for p in item.get("parents", []) for k in kette(p) or [[]]]


print("Eltern:", [" -> ".join(k) for k in kette(items.getItem("Flur_Licht", parents=True))])

print("entfernen:", items.removeGroupMember("gLichter", "Flur_Licht"))
items.deleteItem("Flur_Licht")
