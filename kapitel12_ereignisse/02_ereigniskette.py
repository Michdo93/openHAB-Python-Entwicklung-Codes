"""Kapitel 12: Welche Ereignisse löst ein einziger Command aus?"""

import threading
import time

from openhab import Events, Items, iterSSELines

from buchlib import create_client, parse_zeile, Ereignis

client = create_client()
items, events = Items(client), Events(client)

# Alle Ereignisse zum Deckenlicht: Topic openhab/items/Wohnzimmer_Licht/*
ziel = "Wohnzimmer_Licht"
antwort = events.getEvents(f"openhab/items/{ziel}/*")


def ausloesen() -> None:
    time.sleep(1)
    neu = "OFF" if items.getItemState(ziel) == "ON" else "ON"
    print(f">>> sende Command {neu}\n")
    items.sendCommand(ziel, neu)


threading.Thread(target=ausloesen, daemon=True).start()
ende = time.monotonic() + 3
with antwort as strom:
    for zeile in iterSSELines(strom):
        e = parse_zeile(zeile)
        if isinstance(e, Ereignis) and e.name == ziel:
            print(f"{e.typ:<24} {e.topic.split('/')[-1]:<14} {e.wert}")
        if time.monotonic() > ende:
            break
