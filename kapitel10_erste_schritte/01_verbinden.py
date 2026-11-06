"""Kapitel 10: Verbindung zu openHAB herstellen – mit Token oder Basic Auth."""
import os

from openhab import OpenHABClient, Systeminfo, UUID

URL = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
TOKEN = os.environ.get("OPENHAB_TOKEN")              # API-Token aus der Main UI
USER = os.environ.get("OPENHAB_USER")                # oder Benutzername …
PASSWORD = os.environ.get("OPENHAB_PASSWORD")        # … und Passwort

if TOKEN:
    client = OpenHABClient(URL, token=TOKEN)                         # Variante 1
else:
    client = OpenHABClient(URL, username=USER, password=PASSWORD)    # Variante 2

if not client.isLoggedIn:
    raise SystemExit(f"Keine Verbindung zu {URL}")

# Die Wurzel der REST API: Version und Liste aller Endpunkte
wurzel = client.get("/")
print(f"openHAB {wurzel['runtimeInfo']['version']} unter {URL}")
print(f"  Sprache/Land:   {wurzel['locale']}, Maßsystem {wurzel['measurementSystem']}")
print(f"  Endpunkte:      {len(wurzel['links'])}")

info = Systeminfo(client).getSystemInfo()["systemInfo"]
print(f"  Betriebssystem: {info['osName']} {info['osVersion']} ({info['osArchitecture']})")
print(f"  Java:           {info['javaVersion']} von {info['javaVendor']}")
print(f"  Konfiguration:  {info['configFolder']}")
mib = lambda b: b // 2**20
frei, gesamt = mib(info["freeMemory"]), mib(info["totalMemory"])
print(f"  Speicher:       {frei} von {gesamt} MiB frei")
print(f"  Instanz-UUID:   {UUID(client).getUUID()}")
