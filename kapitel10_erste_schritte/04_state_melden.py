"""Kapitel 10: States melden (postUpdate) – ohne ein Gerät anzusprechen."""
from datetime import datetime

from openhab import Items

from buchlib import create_client

items = Items(create_client())

# Ein Messwert mit Einheit, eine Feuchte und ein Zeitstempel
print(items.postUpdate("Werkstatt_Temperatur", "18.4 °C"))
print(items.postUpdate("Werkstatt_Feuchte", "56"))
print(items.postUpdate("Werkstatt_LetzteMeldung",
                       datetime.now().astimezone().isoformat(timespec="seconds")))

# Ein Contact kennt keine Commands – nur States
print(items.postUpdate("Flur_Haustuer", "OPEN"))

for name in ("Werkstatt_Temperatur", "Werkstatt_Feuchte", "Flur_Haustuer"):
    print(f"{name:<22} = {items.getItemState(name)}")
