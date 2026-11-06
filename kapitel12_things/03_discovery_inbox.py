"""Kapitel 12: Geräte suchen lassen und aus der Inbox übernehmen."""
import os
import time

from openhab import OpenHABClient, Discovery, Inbox, Services, Things

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
discovery, inbox, things = Discovery(client), Inbox(client), Things(client)

# Das Astro-Binding findet "Geräte" für den eingestellten Standort.
# Der Standort ist eine Systemeinstellung – auch sie lässt sich per REST setzen.
services = Services(client)
config = services.getServiceConfig("org.openhab.i18n")
config["location"] = "48.0950,8.6630"            # Breite, Länge (Aldingen)
services.updateServiceConfig("org.openhab.i18n", config)
print("Standort:", services.getServiceConfig("org.openhab.i18n")["location"])

print("Bindings mit Gerätesuche:", discovery.getDiscoveryBindings())
print("Suche läuft, Dauer in s:", discovery.startBindingScan("astro"))
time.sleep(3)

for e in inbox.getDiscoveredThings():
    print(f"  {e['flag']:<8} {e['thingUID']:<18} {e['label']}  {e['properties']}")

# Den Mond übernehmen: aus dem Inbox-Eintrag wird ein Thing
antwort = inbox.approveDiscoveryResult("astro:moon:local", "Mond über Aldingen")
print("\nübernehmen:", antwort)
time.sleep(2)
mond = things.getThing("astro:moon:local")
print(mond["label"], mond["statusInfo"]["status"], f"{len(mond['channels'])} Channels")

# Wieder entfernen – der Eintrag erscheint bei der nächsten Suche erneut
print("löschen:", things.deleteThing("astro:moon:local")["statusInfo"]["status"])
