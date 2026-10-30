"""Kapitel 10: Commands senden – für verschiedene Item-Typen."""
import time

from openhab import Items

from buchlib import create_client

items = Items(create_client())

befehle = [
    ("Wohnzimmer_Licht", "ON"),            # Switch
    ("Wohnzimmer_Dimmer", "60"),           # Dimmer: Prozent
    ("Wohnzimmer_Dimmer", "INCREASE"),     # Dimmer: relativ (+10)
    ("Wohnzimmer_Farblicht", "240,100,80"),  # Color: Farbton,Sättigung,Helligkeit
    ("Kueche_Rollladen", "DOWN"),          # Rollershutter
    ("Haus_Status", "Alle zu Hause"),      # String
]

for name, command in befehle:
    antwort = items.sendCommand(name, command)
    print(f"{name:<22} <- {command:<14} {antwort}")

time.sleep(0.5)        # openHAB verarbeitet Commands asynchron
for name in dict(befehle):
    print(f"{name:<22} = {items.getItemState(name)}")
