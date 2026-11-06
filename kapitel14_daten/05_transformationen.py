"""Kapitel 14: Ein Add-on per REST installieren und eine Transformation anlegen."""
import os
import time

from openhab import OpenHABClient, Addons, Items, Transformations

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
addons, items, trafos = Addons(client), Items(client), Transformations(client)
UID = "config:map:tuer"

# 1. Den MAP-Transformationsdienst installieren (falls noch nicht geschehen)
if not addons.getAddon("transformation-map").get("installed"):
    print("installieren:", addons.installAddon("transformation-map"))
    while "MAP" not in trafos.getTransformationServices():
        time.sleep(1)
print("Transformationsdienste:", trafos.getTransformationServices())

# 2. Eine eigene MAP-Transformation anlegen
print("anlegen:", trafos.updateTransformation(UID, {
    "uid": UID, "label": "Türzustand", "type": "map",
    "configuration": {"function": "OPEN=offen\nCLOSED=geschlossen\nNULL=unbekannt\n"}}))
for t in trafos.getTransformations():
    herkunft = "änderbar" if t["editable"] else "aus Datei"
    print(f"  {t['uid']:<16} {t['type']:<4} {herkunft}")

# 3. Im Anzeigeformat eines Items verwenden
items.addMetadata("Flur_Haustuer", "stateDescription",
                  {"value": " ", "config": {"pattern": f"MAP({UID}):%s"}})
for zustand in ("OPEN", "CLOSED"):
    items.postUpdate("Flur_Haustuer", zustand)
    time.sleep(0.3)                          # postUpdate wird asynchron verarbeitet
    tuer = items.getItem("Flur_Haustuer")
    print(f"Zustand {tuer['state']:<6} -> Anzeige {tuer.get('transformedState')}")

# Aufräumen – das Add-on bleibt installiert
items.removeMetadata("Flur_Haustuer", "stateDescription")
print("löschen:", trafos.deleteTransformation(UID))
