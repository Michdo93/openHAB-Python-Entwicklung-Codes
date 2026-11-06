"""Kapitel 11: Metadaten – Zusatzinformationen, die openHABs Verhalten ändern."""
import json
import os
import time

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)
NAME = "Klingel_Status"

items.addOrUpdateItem(NAME, {"type": "String", "name": NAME, "label": "Klingel",
                             "groupNames": ["gHaus"]})

# 1. stateDescription: Anzeigeformat und erlaubte Werte für Oberflächen
print("stateDescription:", items.addMetadata(NAME, "stateDescription", {
    "value": " ",
    "config": {"pattern": "%s", "readOnly": False,
               "options": "RUHE=Ruhe,KLINGELT=Es klingelt!,GEOEFFNET=Tür geöffnet"}}))

# 2. expire: Zustand fällt nach zehn Sekunden automatisch zurück
print("expire:          ", items.addMetadata(NAME, "expire", {"value": "10s,state=RUHE"}))

# 3. eigener Namensraum: beliebige Daten für die eigene Anwendung
print("eigener:         ", items.addMetadata(NAME, "restbuch", {
    "value": "klingel", "config": {"raum": "Flur", "prioritaet": 2}}))

print("Namensräume:     ", items.getMetadataNamespaces(NAME))

meta = items.getItem(NAME, metadata="stateDescription,expire,restbuch")["metadata"]
print(json.dumps(meta, indent=2, ensure_ascii=False))

# Die Anzeige nutzt die Optionen aus stateDescription
items.postUpdate(NAME, "KLINGELT")
klingel = items.getItem(NAME)
anzeige = {o["value"]: o["label"] for o in klingel["stateDescription"]["options"]}
print("Zustand:", klingel["state"], "| Anzeige:", anzeige[klingel["state"]])

# expire setzt den Zustand nach zehn Sekunden zurück
time.sleep(11)
print("nach 11 s:", items.getItemState(NAME))

print("entfernen:", items.removeMetadata(NAME, "restbuch"))
items.deleteItem(NAME)
