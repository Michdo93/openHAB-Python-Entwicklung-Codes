"""Kapitel 11: Regeln auflisten, ausführen, deaktivieren und aktivieren."""

import time

from openhab import Items, Rules

from buchlib import create_client

client = create_client()
rules, items = Rules(client), Items(client)


def status(uid: str) -> str:
    """Status einer einzelnen Regel lesen."""
    info = rules.getRule(uid)["status"]
    return f"{info['status']} / {info['statusDetail']}"


for regel in rules.getRules():
    print(f"{regel['uid']:<12} {regel['name']:<12} {regel['status']['status']}")

items.sendCommand("Wohnzimmer_Licht", "ON")
time.sleep(0.3)
print(
    "\nvorher: ", items.getItemState("gLichter"), items.getItemState("Haus_Status")
)

rules.runNow("restbuch-1")  # Regel »Gute Nacht« ausführen
time.sleep(0.5)
print("nachher:", items.getItemState("gLichter"), items.getItemState("Haus_Status"))

rules.disable("restbuch-1")
print("\ndeaktiviert:", status("restbuch-1"))
rules.enable("restbuch-1")
print("aktiviert:  ", status("restbuch-1"))
