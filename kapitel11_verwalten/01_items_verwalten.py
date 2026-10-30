"""Kapitel 11: Items per REST anlegen, erweitern und löschen (CRUD)."""
from openhab import Items

from buchlib import create_client

items = Items(create_client())
NAME = "Garten_Pumpe"

# Create – ein neues Item aus einem Python-Dictionary
definition = {
    "type": "Switch",
    "name": NAME,
    "label": "Gartenpumpe",
    "category": "water",
    "tags": ["Switch"],
    "groupNames": ["gHaus"],
}
print("anlegen:   ", items.addOrUpdateItem(NAME, definition))

# Update – Tag, Gruppe und Metadaten ergänzen
print("Tag:       ", items.addTag(NAME, "Pump"))
print("Gruppe:    ", items.addGroupMember("gWerkstatt", NAME))
print("Metadaten: ", items.addMetadata(NAME, "autoupdate", {"value": "false"}))

# Read – das Ergebnis prüfen
pumpe = items.getItem(NAME)
print("gelesen:   ", pumpe["label"], pumpe["tags"], pumpe["groupNames"])

# Delete – und wieder aufräumen
print("löschen:   ", items.deleteItem(NAME))
print("danach:    ", items.getItem(NAME))
