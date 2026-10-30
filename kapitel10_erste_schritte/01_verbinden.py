"""Kapitel 10: Verbindung zu openHAB herstellen und Systeminfo lesen."""
import os

from openhab import OpenHABClient, Systeminfo

url = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
token = os.environ.get("OPENHAB_TOKEN")

if token:                                          # Variante 1: API-Token
    client = OpenHABClient(url, token=token)
else:                                              # Variante 2: Basic Auth
    client = OpenHABClient(url, username=os.environ.get("OPENHAB_USER"),
                           password=os.environ.get("OPENHAB_PASSWORD"))

if not client.isLoggedIn:
    raise SystemExit(f"Keine Verbindung zu {url}")

info = Systeminfo(client).getSystemInfo()["systemInfo"]
print(f"Verbunden mit {url}")
print(f"  Betriebssystem: {info['osName']} {info['osVersion']}")
print(f"  Java:           {info['javaVersion']}")
print(f"  Konfiguration:  {info['configFolder']}")
