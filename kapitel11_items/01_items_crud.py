"""Kapitel 11: Ein Item per REST anlegen, lesen, ändern und löschen (CRUD)."""
import os

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)
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
neu = items.addOrUpdateItem(NAME, definition)
print("angelegt: ", neu["name"], neu["type"], neu["state"])

# Read – und gleich bedienen: ein per REST angelegtes Item ist ein ganz normales Item
items.sendCommand(NAME, "ON")
print("gelesen:  ", items.getItemState(NAME))

# Update – PUT ersetzt die ganze Definition (idempotent)
definition["label"] = "Gartenpumpe Zisterne"
definition["groupNames"] = ["gHaus", "gWerkstatt"]
items.addOrUpdateItem(NAME, definition)
pumpe = items.getItem(NAME)
print("geändert: ", pumpe["label"], pumpe["groupNames"], "Zustand:", pumpe["state"])
print("verwaltet:", "per REST änderbar" if pumpe["editable"] else "aus einer Datei")

# Delete – und wieder aufräumen
print("löschen:  ", items.deleteItem(NAME))
print("danach:   ", items.getItem(NAME))
