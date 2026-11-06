"""Kapitel 12: Ein Thing per REST anlegen, konfigurieren, abschalten und löschen."""
import os
import time

from openhab import OpenHABClient, Things

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
things = Things(client)
UID = "astro:moon:buch"


def status() -> str:
    s = things.getThingStatus(UID)
    detail = "" if s["statusDetail"] == "NONE" else f" / {s['statusDetail']}"
    return s["status"] + detail


neu = things.createThing({
    "UID": UID, "thingTypeUID": "astro:moon", "label": "Mond (per REST)",
    "configuration": {"geolocation": "48.0950,8.6630", "interval": 300},
})
print("angelegt:", neu["UID"], f"mit {len(neu['channels'])} Channels")
time.sleep(2)
print("Status:  ", status())

# Konfiguration ändern – openHAB initialisiert das Thing neu
things.updateThingConfiguration(UID, {"geolocation": "52.5200,13.4050", "interval": 60})
print("Ort:     ", things.getThing(UID)["configuration"]["geolocation"], "(Berlin)")

# Label ändern: updateThing ersetzt die ganze Definition
thing = things.getThing(UID)
thing["label"] = "Mond über Berlin"
print("Label:   ", things.updateThing(UID, thing)["label"])

# Abschalten und wieder einschalten
things.disableThing(UID)
time.sleep(1)
print("aus:     ", status())
things.enableThing(UID)
time.sleep(2)
print("an:      ", status())

print("löschen: ", things.deleteThing(UID)["statusInfo"]["status"])
print("Things:  ", [t["UID"] for t in things.getThings(summary=True)])
