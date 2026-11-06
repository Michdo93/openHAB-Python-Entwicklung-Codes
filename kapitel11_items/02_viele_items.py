"""Kapitel 11: Einen ganzen Raum mit einem einzigen Aufruf anlegen."""
import os

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)


def item(typ: str, name: str, label: str, gruppen: list, tags: list, **mehr) -> dict:
    return {"type": typ, "name": name, "label": label,
            "groupNames": gruppen, "tags": tags, **mehr}


gartenhaus = [
    item("Group", "gGartenhaus", "Gartenhaus", ["gHaus"], ["Garden"]),
    item("Switch", "Gartenhaus_Licht", "Licht", ["gGartenhaus"], ["Switch", "Light"],
         category="light"),
    item("Number:Temperature", "Gartenhaus_Temperatur", "Temperatur", ["gGartenhaus"],
         ["Measurement", "Temperature"], category="temperature"),
    item("Contact", "Gartenhaus_Tuer", "Tür", ["gGartenhaus"], ["OpenState", "Door"],
         category="door"),
    item("Group", "gGartenhaus_Lichter", "Lichter im Gartenhaus", ["gGartenhaus"], [],
         groupType="Switch", function={"name": "OR", "params": ["ON", "OFF"]}),
]
gartenhaus[1]["groupNames"].append("gGartenhaus_Lichter")

print("anlegen:", items.addOrUpdateItems(gartenhaus))
items.postUpdate("Gartenhaus_Temperatur", "12.5 °C")
items.postUpdate("Gartenhaus_Tuer", "CLOSED")
items.sendCommand("Gartenhaus_Licht", "ON")

raum = items.getItem("gGartenhaus", recursive=True)
for m in sorted(raum["members"], key=lambda m: m["name"]):
    print(f"  {m['name']:<24} {m['type']:<20} {m['state']}")

# Die Gruppenfunktion OR(ON,OFF) fasst die Mitglieder zusammen
print("Lichter im Gartenhaus:", items.getItemState("gGartenhaus_Lichter"))

# Aufräumen: zuerst die Mitglieder, dann die Gruppen
for i in reversed(gartenhaus):
    items.deleteItem(i["name"])
print("aufgeräumt:", "error" in items.getItem("gGartenhaus"))
