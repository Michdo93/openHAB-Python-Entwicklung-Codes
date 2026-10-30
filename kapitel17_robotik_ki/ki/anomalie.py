"""
Kapitel 17: Auffällige Messwerte in der Persistenz erkennen.

Verfahren: gleitender Median und robuste Streuung (MAD). Ein Wert gilt
als Ausreißer, wenn er mehr als SCHWELLE robuste Standardabweichungen
vom Median seiner Nachbarn abweicht. Das Ergebnis wird als Text an
openHAB zurückgemeldet – und steht damit Regeln und Oberflächen zur
Verfügung.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median

from openhab import Items, Persistence

from buchlib import als_zahl, create_client

FENSTER = 8  # Nachbarn links und rechts
SCHWELLE = 6.0  # robuste Standardabweichungen
DIENST = "inmemory"  # Testdaten aus Kapitel 11; im Alltag z. B. "rrd4j"


def lade_verlauf(persistence: Persistence, item: str, stunden: int = 48):
    ende = datetime.now(timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    antwort = persistence.getItemPersistenceData(
        item,
        DIENST,
        (ende - timedelta(hours=stunden)).strftime(fmt),
        ende.strftime(fmt),
    )
    return [
        (datetime.fromtimestamp(p["time"] / 1000), als_zahl(p["state"]))
        for p in antwort.get("data", [])
        if als_zahl(p["state"]) is not None
    ]


def finde_ausreisser(reihe):
    werte = [w for _, w in reihe]
    treffer = []
    for i, (zeit, wert) in enumerate(reihe):
        nachbarn = werte[max(0, i - FENSTER) : i] + werte[i + 1 : i + 1 + FENSTER]
        if len(nachbarn) < FENSTER:
            continue
        mitte = median(nachbarn)
        mad = median(abs(x - mitte) for x in nachbarn) * 1.4826 or 0.05
        abstand = abs(wert - mitte) / mad
        if abstand > SCHWELLE:
            treffer.append((zeit, wert, mitte, abstand))
    return treffer


def main() -> None:
    client = create_client()
    persistence, items = Persistence(client), Items(client)
    for item in ("Werkstatt_Temperatur", "Wohnzimmer_Temperatur"):
        reihe = lade_verlauf(persistence, item)
        treffer = finde_ausreisser(reihe)
        print(f"{item}: {len(reihe)} Werte, {len(treffer)} Auffälligkeit(en)")
        for zeit, wert, mitte, abstand in treffer:
            print(
                f"   {zeit:%d.%m. %H:%M}  {wert:.1f} °C  "
                f"(erwartet ~{mitte:.1f}, {abstand:.0f} sigma)"
            )
        if treffer:
            zeit, wert, *_ = treffer[-1]
            items.postUpdate(
                "Haus_Status", f"Auffällig: {item} {wert:.1f} °C um {zeit:%H:%M}"
            )


if __name__ == "__main__":
    main()
