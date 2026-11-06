"""Kapitel 11: Das semantische Modell – Orte, Ausstattung und Messpunkte per REST."""
import os

from openhab import OpenHABClient, Items, Tags

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, tags = Items(client), Tags(client)

# 1. Der Tag-Katalog: Hunderte vordefinierte semantische Tags, auf Deutsch übersetzt
katalog = tags.getTags(language="de")
orte = [t for t in katalog if t["uid"].startswith("Location_")]
print(f"{len(katalog)} Tags, davon {len(orte)} Orte, z. B.:",
      ", ".join(t["label"] for t in orte[:6]))

# 2. openHAB leitet aus den Tags Metadaten im Namensraum 'semantics' ab
for item in items.getItems(metadata="semantics", fields="name,label,metadata"):
    sem = item.get("metadata", {}).get("semantics")
    if sem:
        cfg = sem.get("config", {})
        print(f"  {item['name']:<24} {sem['value']:<26} "
              f"{cfg.get('relatesTo', ''):<22} {cfg.get('hasLocation', '')}")

# 3. Wo befindet sich ein Messpunkt? openHAB folgt dem Modell nach oben.
ort = items.getSemanticItem("Wohnzimmer_Temperatur", "Location")
print("\nWohnzimmer_Temperatur liegt in:", ort["name"], f"({ort['label']})")

# 4. Ein eigener Ort: das Tag wird per REST angelegt und sofort nutzbar
print("\nTag anlegen:", tags.createTag({
    "uid": "Location_Outdoor_Garden_Gartenhaus", "name": "Gartenhaus",
    "label": "Gartenhaus", "description": "Hütte im Garten", "synonyms": ["Schuppen"]}))
items.addOrUpdateItem("gGartenhaus", {"type": "Group", "name": "gGartenhaus",
                                      "label": "Gartenhaus", "tags": ["Gartenhaus"],
                                      "groupNames": ["gHaus"]})
items.addOrUpdateItem("Gartenhaus_Temperatur", {
    "type": "Number:Temperature", "name": "Gartenhaus_Temperatur", "label": "Temperatur",
    "tags": ["Measurement", "Temperature"], "groupNames": ["gGartenhaus"]})
print("Semantik:", items.getItem("Gartenhaus_Temperatur", metadata="semantics")
      ["metadata"]["semantics"])

for name in ("Gartenhaus_Temperatur", "gGartenhaus"):
    items.deleteItem(name)
print("Tag löschen:", tags.deleteTag("Location_Outdoor_Garden_Gartenhaus"))
