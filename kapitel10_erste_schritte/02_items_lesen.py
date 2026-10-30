"""Kapitel 10: Items lesen – alle, eines, nur den Zustand."""
from openhab import Items

from buchlib import create_client

items = Items(create_client())

# 1. Alle Items, auf drei Felder beschränkt (spart Daten)
alle = items.getItems(fields="name,type,state")
print(f"{len(alle)} Items gefunden:")
for item in sorted(alle, key=lambda i: i["name"]):
    print(f"  {item['name']:<28} {item['type']:<22} {item['state']}")

# 2. Ein einzelnes Item mit allen Details
licht = items.getItem("Wohnzimmer_Licht")
print("\nLabel:", licht["label"], "| Gruppen:", licht["groupNames"],
      "| Tags:", licht["tags"])

# 3. Nur der Zustand – als reiner Text
print("Temperatur:", items.getItemState("Wohnzimmer_Temperatur"))

# 4. Filter: alle Items eines Typs, alle Items mit einem Tag
dimmer = items.getItems(type="Dimmer", fields="name")
lichter = items.getItems(tags="Light", fields="name")
print("Dimmer:", [i["name"] for i in dimmer])
print("Mit Tag 'Light':", [i["name"] for i in lichter])
