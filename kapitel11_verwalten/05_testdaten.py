"""Kapitel 11: Testdaten in einen schreibbaren Persistenzdienst schreiben.

Eine frische Installation hat noch keine Vergangenheit. Dieses Skript
schreibt 48 Stunden synthetische Temperaturwerte (alle 15 Minuten) in den
Dienst »inmemory« – einschließlich eines Ausreißers für Kapitel 17.
rrd4j ist nicht schreibbar und lehnt storeItemData mit 400 ab.
"""
import math
import random
from datetime import datetime, timedelta, timezone

from openhab import Persistence

from buchlib import create_client

DIENST = "inmemory"
persistence = Persistence(create_client())
rnd = random.Random(42)  # gleiche Zufallszahlen bei jedem Lauf
jetzt = datetime.now(timezone.utc).replace(second=0, microsecond=0)

for item, basis in (("Wohnzimmer_Temperatur", 21.0), ("Werkstatt_Temperatur", 17.0)):
    persistence.deleteItemData(item, (jetzt - timedelta(days=3)).isoformat(),
                               jetzt.isoformat(), DIENST)  # alte Testdaten weg
    for k in range(48 * 4, 0, -1):
        zeit = jetzt - timedelta(minutes=15 * k)
        stunde = zeit.hour + zeit.minute / 60
        wert = basis + 1.5 * math.sin((stunde - 9) / 24 * 2 * math.pi)
        wert += rnd.gauss(0, 0.15)
        if item == "Werkstatt_Temperatur" and k == 30:
            wert += 6.0  # ein Ausreißer
        antwort = persistence.storeItemData(
            item, zeit.strftime("%Y-%m-%dT%H:%M:%S.000Z"), f"{wert:.2f} °C", DIENST)
        if "error" in antwort:
            raise SystemExit(f"{item}: {antwort['error']}")
    print(f"{item}: 192 Werte in »{DIENST}« geschrieben")

# Gegenprobe: rrd4j nimmt keine Werte von außen an
antwort = persistence.storeItemData("Wohnzimmer_Temperatur",
                                    jetzt.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "20 °C", "rrd4j")
print("Gegenprobe rrd4j:", antwort["error"].rsplit("(", 1)[-1].rstrip(")"))
