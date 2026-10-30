"""Kapitel 12: Den Ereignisstrom direkt lesen – Zeile für Zeile."""

import json

from openhab import ItemEvents, iterSSELines

from buchlib import create_client

item_events = ItemEvents(create_client())

# Alle Zustandsänderungen aller Items (Topic openhab/items/*/statechanged)
antwort = item_events.ItemStateChangedEvent()

print("Warte auf Ereignisse … (Strg+C beendet)")
try:
    with antwort as strom:
        for zeile in iterSSELines(strom):  # jede Zeile, sobald sie da ist
            if not zeile.startswith("data:"):  # event:-, Kommentar- und Leerzeilen
                continue
            ereignis = json.loads(zeile[5:])  # 1. JSON: das Ereignis
            if ereignis.get("type") == "ALIVE":
                continue
            payload = json.loads(ereignis["payload"])  # 2. JSON: die Nutzdaten
            name = ereignis["topic"].split("/")[2]
            print(f"{name:<24} {payload['oldValue']:>12} -> {payload['value']}")
except KeyboardInterrupt:
    print("\nbeendet")
