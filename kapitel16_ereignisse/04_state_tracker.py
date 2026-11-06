"""Kapitel 16: Der State-Tracker – nur ausgewählte Items, fertig formatiert."""
import os
import threading
import time

from openhab import OpenHABClient, Events, Items, iterSSELines, parseSSEData

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
events, items = Events(client), Items(client)
SEITE_1 = ["Wohnzimmer_Dimmer", "Wohnzimmer_Temperatur"]
SEITE_2 = ["Werkstatt_Temperatur", "Werkstatt_Feuchte"]


def bedienen() -> None:
    time.sleep(1)
    items.sendCommand("Wohnzimmer_Dimmer", "55")
    items.postUpdate("Werkstatt_Temperatur", "19.3 °C")    # (noch) nicht abonniert
    time.sleep(1)
    print("--- Seitenwechsel: neue Item-Liste")
    events.updateSSEConnectionItems(verbindung, SEITE_2)
    time.sleep(1)
    items.postUpdate("Werkstatt_Temperatur", "19.8 °C")
    time.sleep(1)
    fertig.set()
    items.postUpdate("Werkstatt_Feuchte", items.getItemState("Werkstatt_Feuchte"))


fertig = threading.Event()
verbindung = None
with events.initiateStateTracker() as strom:
    for zeile in iterSSELines(strom):
        if verbindung is None and zeile.startswith("data:"):
            verbindung = zeile[5:].strip()        # 1. Nachricht: die Verbindungskennung
            print("Verbindung:", verbindung)
            events.updateSSEConnectionItems(verbindung, SEITE_1)
            threading.Thread(target=bedienen, daemon=True).start()
            continue
        daten = parseSSEData(zeile)
        if isinstance(daten, dict) and daten.get("type") != "ALIVE":
            for name, z in daten.items():
                anzeige = z.get("displayState", z["state"])     # formatiert wie in der UI
                print(f"  {name:<22} state={z['state']:<38} anzeige={anzeige}")
        if fertig.is_set():
            break
