"""Kapitel 16: Welche Ereignisse löst ein einziger Command aus?"""
import os
import threading
import time

from openhab import OpenHABClient, Events, Items, iterSSEEvents

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, events = Items(client), Events(client)
ZIEL = "Wohnzimmer_Licht"


def ausloesen() -> None:
    time.sleep(1)
    neu = "OFF" if items.getItemState(ZIEL) == "ON" else "ON"
    print(f">>> sende Command {neu}\n")
    items.sendCommand(ZIEL, neu)


threading.Thread(target=ausloesen, daemon=True).start()
ende = time.monotonic() + 3
# Alle Ereignisse dieses Items: Topic openhab/items/Wohnzimmer_Licht/*
with events.getEvents(f"openhab/items/{ZIEL}/*") as strom:
    for e in iterSSEEvents(strom, includeAlive=True):     # payload schon entpackt
        if "topic" in e:
            art = e["topic"].split("/")[-1]
            print(f"{e['type']:<24} {art:<13} {e['payload']['value']}")
        if time.monotonic() > ende:
            break
