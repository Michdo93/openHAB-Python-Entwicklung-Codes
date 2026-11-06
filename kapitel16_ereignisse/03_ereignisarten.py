"""Kapitel 16: Ein Strom für vieles – Items, Things und Links gleichzeitig beobachten."""
import os
import threading
import time

from openhab import OpenHABClient, Events, Items, Links, Things, iterSSEEvents

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, things, links = Items(client), Things(client), Links(client)
SONNE = "astro:sun:zuhause"

THEMEN = ",".join([
    "openhab/items/Sonne_Azimut/added",        # Item angelegt
    "openhab/items/Sonne_Azimut/removed",      # Item gelöscht
    "openhab/items/Sonne_Azimut/statechanged", # Zustand geändert
    "openhab/things/*/statuschanged",          # Statuswechsel aller Things
    "openhab/links/*/*",                        # neue und gelöschte Links
])


def aktionen() -> None:
    """Erzeugt nacheinander typische Ereignisse."""
    time.sleep(1)
    items.addOrUpdateItem("Sonne_Azimut", {"type": "Number:Angle", "name": "Sonne_Azimut",
                                           "label": "Sonnenrichtung"})
    links.linkItemToChannel("Sonne_Azimut", f"{SONNE}:position#azimuth", {})
    time.sleep(1)
    things.disableThing(SONNE)
    time.sleep(1)
    things.enableThing(SONNE)
    time.sleep(2)
    links.unlinkItemFromChannel("Sonne_Azimut", f"{SONNE}:position#azimuth")
    items.deleteItem("Sonne_Azimut")
    time.sleep(1)
    fertig.set()
    items.postUpdate("Haus_Status", items.getItemState("Haus_Status"))   # wecken


fertig = threading.Event()
threading.Thread(target=aktionen, daemon=True).start()
with Events(client).getEvents(THEMEN + ",openhab/items/Haus_Status/state") as strom:
    for e in iterSSEEvents(strom, includeAlive=True):
        if fertig.is_set():
            break
        if "topic" not in e:
            continue
        p = e["payload"]
        if e["type"] == "ThingStatusInfoChangedEvent":
            neu, alt = p                                        # Liste [neu, alt]
            info = f"{alt['status']} -> {neu['status']} ({neu['statusDetail']})"
        elif e["type"].startswith("ItemChannelLink"):
            info = f"{p['itemName']} <-> {p['channelUID'].split(':')[-1]}"
        elif isinstance(p, dict):
            info = p.get("value", p.get("name", ""))
        else:
            info = ""
        print(f"{e['type']:<34} {info}")
