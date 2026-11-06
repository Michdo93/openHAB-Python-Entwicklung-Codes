"""Kapitel 10: Commands senden – für verschiedene Item-Typen."""
import os
import time

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)

befehle = [
    ("Wohnzimmer_Licht", "ON"),              # Switch
    ("Wohnzimmer_Dimmer", "60"),             # Dimmer: Prozent
    ("Wohnzimmer_Farblicht", "240,100,80"),  # Color: Farbton,Sättigung,Helligkeit
    ("Kueche_Rollladen", "DOWN"),            # Rollershutter
    ("Haus_Status", "Alle zu Hause"),        # String
]

for name, command in befehle:
    antwort = items.sendCommand(name, command, source="buch:kapitel10")
    print(f"{name:<22} <- {command:<14} {antwort}")

time.sleep(0.5)        # openHAB verarbeitet Commands asynchron
for name, _ in befehle:
    print(f"{name:<22} = {items.getItemState(name)}")
