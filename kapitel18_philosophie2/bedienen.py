"""Kapitel 18: Die virtuellen Geräte bedienen – wie es die Main UI täte."""
import os
import time

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)

for name, command, pause in (("Werkstatt_Luefter", "ON", 2),
                             ("Kueche_Rollladen", "DOWN", 1.5),
                             ("Kueche_Rollladen", "STOP", 1),
                             ("Kueche_Rollladen", "20", 4),
                             ("Werkstatt_Luefter", "OFF", 1)):
    print(f"{time.strftime('%H:%M:%S')} Command {name} <- {command}")
    items.sendCommand(name, command)
    time.sleep(pause)
    print(f"{time.strftime('%H:%M:%S')}   {name} = {items.getItemState(name)}")
