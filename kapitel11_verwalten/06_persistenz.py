"""Kapitel 11: Historische Werte abfragen und auswerten."""
from datetime import datetime, timedelta, timezone
from statistics import mean

from openhab import Persistence

from buchlib import create_client, als_zahl

DIENST = "inmemory"  # Testdaten aus 05_testdaten.py; im Alltag meist "rrd4j"
persistence = Persistence(create_client())

ende = datetime.now(timezone.utc)
start = ende - timedelta(hours=24)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")   # Format der REST API

antwort = persistence.getItemPersistenceData(
    "Wohnzimmer_Temperatur", DIENST, iso(start), iso(ende))

punkte = [(datetime.fromtimestamp(p["time"] / 1000), als_zahl(p["state"]))
          for p in antwort.get("data", [])]
werte = [w for _, w in punkte if w is not None]

print(f"{len(werte)} Messwerte der letzten 24 Stunden")
print(f"Minimum {min(werte):.1f} °C   Maximum {max(werte):.1f} °C   "
      f"Mittel {mean(werte):.1f} °C")

# Ein Verlauf als Textdiagramm – stündliche Werte
BALKEN = " .:-=+*#%@"
stuendlich = werte[::4]
lo, hi = min(stuendlich), max(stuendlich)
stufen = len(BALKEN) - 1
print("".join(BALKEN[round((w - lo) / (hi - lo or 1) * stufen)] for w in stuendlich))
