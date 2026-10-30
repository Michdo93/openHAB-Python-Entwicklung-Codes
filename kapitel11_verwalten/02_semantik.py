"""Kapitel 11: Das Haus über Gruppen und Tags erkunden statt Namen zu codieren."""

from openhab import Items

from buchlib import create_client, ist_bekannt

items = Items(create_client())


def zeige_baum(item: dict, tiefe: int = 0) -> None:
    """Gibt eine Gruppe mit allen Mitgliedern rekursiv aus."""
    zustand = item.get("state", "")
    zusatz = (
        f" = {zustand}" if item["type"] != "Group" and ist_bekannt(zustand) else ""
    )
    print("    " * tiefe + f"{item['name']} ({item['type']}){zusatz}")
    for mitglied in sorted(item.get("members", []), key=lambda m: m["name"]):
        zeige_baum(mitglied, tiefe + 1)


zeige_baum(items.getItem("gHaus", recursive=True))

# Alle Temperatur-Messpunkte – egal, wie sie heißen
temperaturen = items.getItems(tags="Temperature", fields="name,label,state")
print("\nTemperaturen im Haus:")
for t in temperaturen:
    print(f"  {t['label']:<12} {t['state']}")
