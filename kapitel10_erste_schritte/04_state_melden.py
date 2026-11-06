"""Kapitel 10: States melden (postUpdate) – ohne ein Gerät anzusprechen."""
import os
from datetime import datetime

from openhab import OpenHABClient, Items

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items = Items(client)

# Ein Messwert mit Einheit, eine Feuchte und ein Zeitstempel
print(items.postUpdate("Werkstatt_Temperatur", "18.4 °C"))
print(items.postUpdate("Werkstatt_Feuchte", "56 %"))
print(items.postUpdate("Werkstatt_LetzteMeldung",
                       datetime.now().astimezone().isoformat(timespec="seconds")))

# Ein Contact kennt keine Commands – nur States
print(items.postUpdate("Flur_Haustuer", "OPEN"))

# Einheiten werden umgerechnet: Fahrenheit rein, Celsius raus
print(items.postUpdate("Wohnzimmer_Temperatur", "71.6 °F"))

for name in ("Werkstatt_Temperatur", "Werkstatt_Feuchte", "Flur_Haustuer",
             "Wohnzimmer_Temperatur"):
    print(f"{name:<22} = {items.getItemState(name)}")

# Die Umrechnung ist exakt, aber nicht schön: Anzeigen formatieren mit dem Muster
# des Items (hier %.1f °C). Für die weiteren Beispiele wieder 21.5 °C setzen.
items.postUpdate("Wohnzimmer_Temperatur", "21.5 °C")
