"""Kapitel 14: Gespeicherte Werte gezielt löschen."""
import os
from datetime import datetime, timedelta, timezone

from openhab import OpenHABClient, Persistence

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
persistence = Persistence(client)
DIENST = "inmemory"
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
jetzt = datetime.now(timezone.utc)


def anzahl() -> str:
    return persistence.getItemPersistenceData("Werkstatt_Temperatur", DIENST,
                                              iso(jetzt - timedelta(days=3)),
                                              iso(jetzt))["datapoints"]


print("vorher: ", anzahl())
# Nur die Nacht von 0 bis 6 Uhr (UTC) von gestern löschen
gestern = (jetzt - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
print(persistence.deleteItemData("Werkstatt_Temperatur", iso(gestern),
                                 iso(gestern + timedelta(hours=6)), DIENST))
print("nachher:", anzahl())

# rrd4j lehnt das Löschen ab – genau wie das Schreiben
antwort = persistence.deleteItemData("Werkstatt_Temperatur", iso(gestern), iso(jetzt),
                                     "rrd4j")
print("rrd4j:", antwort["error"].rsplit("(", 1)[-1].rstrip(")"))
