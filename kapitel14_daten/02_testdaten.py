"""Kapitel 14: Werte mit eigenem Zeitstempel in einen Persistenzdienst schreiben.

Eine frische Installation hat noch keine Vergangenheit. Dieses Skript schreibt
48 Stunden synthetische Temperaturwerte (alle 15 Minuten) in den Dienst
»inmemory« – einschließlich eines Ausreißers, den Kapitel 20 wiederfindet.
"""
import math
import os
import random
from datetime import datetime, timedelta, timezone

from openhab import OpenHABClient, Persistence

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
persistence = Persistence(client)
DIENST = "inmemory"
rnd = random.Random(42)                    # gleiche Zufallszahlen bei jedem Lauf
jetzt = datetime.now(timezone.utc).replace(second=0, microsecond=0)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

for item, basis in (("Wohnzimmer_Temperatur", 21.0), ("Werkstatt_Temperatur", 17.0)):
    # alte Testdaten der letzten drei Tage entfernen
    persistence.deleteItemData(item, iso(jetzt - timedelta(days=3)), iso(jetzt), DIENST)
    for k in range(48 * 4, 0, -1):
        zeit = jetzt - timedelta(minutes=15 * k)
        stunde = zeit.hour + zeit.minute / 60
        wert = basis + 1.5 * math.sin((stunde - 9) / 24 * 2 * math.pi) + rnd.gauss(0, 0.15)
        if item == "Werkstatt_Temperatur" and k == 30:
            wert += 6.0                    # ein Ausreißer
        antwort = persistence.storeItemData(item, iso(zeit), f"{wert:.2f} °C", DIENST)
        if "error" in antwort:
            raise SystemExit(f"{item}: {antwort['error']}")
    print(f"{item}: 192 Werte in »{DIENST}« geschrieben")

# Gegenprobe: rrd4j nimmt keine Werte von außen an
antwort = persistence.storeItemData("Wohnzimmer_Temperatur", iso(jetzt), "20 °C", "rrd4j")
print("Gegenprobe rrd4j:", antwort["error"].rsplit("(", 1)[-1].rstrip(")"))
