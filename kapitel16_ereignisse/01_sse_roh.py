"""Kapitel 16: Den Ereignisstrom direkt lesen – Zeile für Zeile."""
import json
import os

from openhab import OpenHABClient, ItemEvents, iterSSELines

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))

# Alle Zustandsänderungen aller Items (Topic openhab/items/*/statechanged)
strom = ItemEvents(client).ItemStateChangedEvent()

print("Warte auf Ereignisse … (Strg+C beendet)")
try:
    with strom:
        for zeile in iterSSELines(strom):          # jede Zeile, sobald sie da ist
            print("roh:", zeile[:70])
            if not zeile.startswith("data:"):      # event:-, id:- und Leerzeilen
                continue
            ereignis = json.loads(zeile[5:])       # 1. JSON: das Ereignis
            if ereignis.get("type") == "ALIVE":    # Lebenszeichen, kein Ereignis
                continue
            payload = json.loads(ereignis["payload"])   # 2. JSON: die Nutzdaten
            name = ereignis["topic"].split("/")[2]
            print(f"  -> {name}: {payload['oldValue']} -> {payload['value']}")
except KeyboardInterrupt:
    print("\nbeendet")
