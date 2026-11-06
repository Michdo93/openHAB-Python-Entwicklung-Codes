"""Kapitel 12: Thing-Typen, Channel-Typen und Konfigurationsbeschreibungen lesen."""
import os

from openhab import OpenHABClient, ThingTypes, ChannelTypes, ConfigDescriptions

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))

typen = ThingTypes(client).getThingTypes(bindingID="astro", language="de")
for t in typen:
    print(f"{t['UID']:<12} {t['label']}")

mond = ThingTypes(client).getThingType("astro:moon", language="de")
print(f"\n{mond['label']} – Channel-Gruppen:")
for gruppe in mond["channelGroups"]:
    kanaele = ", ".join(k["id"] for k in gruppe["channels"])
    print(f"  {gruppe['id']:<10} {kanaele}")

# Welche Konfiguration braucht ein Mond-Thing?
beschreibung = ConfigDescriptions(client).getConfigDescription(
    "thing-type:astro:moonconfig", language="de")
print("\nKonfiguration:")
for p in beschreibung["parameters"]:
    pflicht = "Pflicht" if p.get("required") else f"Standard {p.get('default', '–')}"
    print(f"  {p['name']:<12} {p['type']:<8} {pflicht:<16} {p['label']}")

# Ein Channel-Typ verrät, zu welchem Item-Typ er passt
kanal = ChannelTypes(client).getChannelType("astro:phaseName", language="de")
print(f"\nChannel-Typ {kanal['UID']}: {kanal['label']}, Item-Typ {kanal['itemType']}")
print("Optionen:", [o["label"] for o in kanal["stateDescription"]["options"]][:8])
