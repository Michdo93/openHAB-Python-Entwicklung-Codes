"""Kapitel 14: Historische Werte abfragen und auswerten."""
import os
from datetime import datetime, timedelta, timezone
from statistics import mean

from openhab import OpenHABClient, Persistence

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
persistence = Persistence(client)
DIENST = "inmemory"                   # Testdaten aus 02_testdaten.py
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

ende = datetime.now(timezone.utc)
start = ende - timedelta(hours=24)
antwort = persistence.getItemPersistenceData("Wohnzimmer_Temperatur", DIENST,
                                             iso(start), iso(ende))

punkte = [(datetime.fromtimestamp(p["time"] / 1000), float(p["state"].split()[0]))
          for p in antwort["data"]]
werte = [w for _, w in punkte]
print(f"{antwort['datapoints']} Messwerte der letzten 24 Stunden")
print(f"Minimum {min(werte):.1f} °C   Maximum {max(werte):.1f} °C   "
      f"Mittel {mean(werte):.1f} °C")
warm = max(punkte, key=lambda p: p[1])
print(f"am wärmsten um {warm[0]:%H:%M} Uhr")

# Ein Verlauf als Textdiagramm – stündliche Werte
BALKEN = " .:-=+*#%@"
stuendlich = werte[::4]
lo, hi = min(stuendlich), max(stuendlich)
print("".join(BALKEN[round((w - lo) / (hi - lo) * (len(BALKEN) - 1))] for w in stuendlich))

# Seitenweise abrufen: 10 Werte pro Seite, Seite 0 ist die erste
seite = persistence.getItemPersistenceData("Wohnzimmer_Temperatur", DIENST,
                                           iso(start), iso(ende), page=0, pageLength=10)
print("Seite 0:", [p["state"] for p in seite["data"][:3]], "…")

# Mit boundary=True liefert openHAB zusätzlich den Wert vor und nach dem Zeitraum
rand = persistence.getItemPersistenceData("Wohnzimmer_Temperatur", DIENST,
                                          iso(ende - timedelta(minutes=5)), iso(ende),
                                          boundary=True)
print("letzte 5 Minuten mit Rand:", rand["datapoints"], "Werte")
