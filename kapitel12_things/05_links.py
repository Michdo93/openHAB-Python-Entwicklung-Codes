"""Kapitel 12: Items mit Channels verknüpfen – mit und ohne Profil."""
import os
import time

from openhab import OpenHABClient, Items, Links, ProfileTypes

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, links = Items(client), Links(client)
SONNE = "astro:sun:zuhause"

# Zwei neue Items für Sonnenhöhe und Tagesphase
items.addOrUpdateItem("Sonne_Hoehe", {"type": "Number:Angle", "name": "Sonne_Hoehe",
                                      "label": "Sonnenhöhe", "groupNames": ["gHaus"]})
items.addOrUpdateItem("Sonne_Phase", {"type": "String", "name": "Sonne_Phase",
                                      "label": "Tagesphase", "groupNames": ["gHaus"]})

# Welche Profile passen zwischen diesen Channel und ein Number:Angle-Item?
profile = ProfileTypes(client).getProfileTypes(channelTypeUID="astro:elevation",
                                               itemType="Number:Angle")
print("passende Profile:", [p["uid"] for p in profile])

# Link ohne Profil und Link mit Profil "offset" (+90° -> 0° bis 180°)
print("Link 1:", links.linkItemToChannel("Sonne_Phase", f"{SONNE}:phase#name", {}))
print("Link 2:", links.linkItemToChannel("Sonne_Hoehe", f"{SONNE}:position#elevation",
                                         {"profile": "system:offset", "offset": "90 °"}))
time.sleep(2)                       # das Binding liefert den Wert beim Verknüpfen
print("Sonne_Phase =", items.getItemState("Sonne_Phase"))
print("Sonne_Hoehe =", items.getItemState("Sonne_Hoehe"), "(Höhe + 90°)")

for link in links.getLinks(itemName="Sonne_Hoehe"):
    print("gespeichert:", link["itemName"], "->", link["channelUID"], link["configuration"])

# Aufräumen: Links lösen, Items löschen, verwaiste Links prüfen
print("lösen:", links.unlinkItemFromChannel("Sonne_Phase", f"{SONNE}:phase#name"))
print("alle Links des Items löschen:", links.deleteAllLinks("Sonne_Hoehe"))
for name in ("Sonne_Hoehe", "Sonne_Phase"):
    items.deleteItem(name)
print("verwaiste Links:", links.getOrphanLinks())
