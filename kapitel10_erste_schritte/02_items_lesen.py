"""Kapitel 10: Items lesen – alle, eines, nur den Zustand."""
import os

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)

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
