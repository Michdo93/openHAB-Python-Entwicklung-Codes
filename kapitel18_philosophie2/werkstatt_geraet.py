"""Kapitel 18: Ein virtuelles Gerät, das sich wie ein echtes in openHAB einbindet.

Philosophie 2: Das Programm ist die Quelle der Wahrheit für seine Items.
  * Es MELDET Messwerte und Zustände per postUpdate (wie ein Binding).
  * Es EMPFÄNGT Commands über den Ereignisstrom und bestätigt sie per postUpdate.
  * Es meldet sich mit einem Lebenszeichen an, das openHAB per expire überwacht.
"""
import argparse
import logging
import os
import random
import threading
import time
from datetime import datetime

from openhab import OpenHABClient, ItemEvents, Items, iterSSEEvents

log = logging.getLogger("werkstatt")
LUEFTER, TEMP, FEUCHTE = "Werkstatt_Luefter", "Werkstatt_Temperatur", "Werkstatt_Feuchte"
MELDUNG, ONLINE = "Werkstatt_LetzteMeldung", "Werkstatt_Online"
GRENZE_C = 24.0                                    # ab hier lüftet das Gerät selbst


class SimulierterSensor:
    """Ersetzt einen echten Sensor: Temperatur steigt, Lüfter kühlt."""

    def __init__(self) -> None:
        self.temperatur, self.feuchte = 21.0, 55.0

    def messen(self, luefter_an: bool) -> tuple[float, float]:
        aenderung = random.uniform(-0.6, -0.2) if luefter_an else random.uniform(0.1, 0.9)
        self.temperatur += aenderung
        self.feuchte = min(95, max(20, self.feuchte + random.uniform(-2, 2)))
        return round(self.temperatur, 1), round(self.feuchte)


class WerkstattGeraet:
    def __init__(self, client: OpenHABClient, intervall: float):
        self.client, self.items = client, Items(client)
        self.sensor, self.luefter_an = SimulierterSensor(), False
        self.intervall, self.stopp = intervall, threading.Event()

    # --- Anmelden: eigenes Item für das Lebenszeichen anlegen (falls nötig) ---------
    def anmelden(self) -> None:
        if "error" in self.items.getItem(ONLINE):
            self.items.addOrUpdateItem(ONLINE, {
                "type": "Switch", "name": ONLINE, "label": "Werkstatt-Gerät erreichbar",
                "groupNames": ["gWerkstatt"], "tags": ["Status"]})
        # fällt nach 3 Intervallen ohne Meldung automatisch auf OFF
        self.items.addMetadata(ONLINE, "expire",
                               {"value": f"{int(self.intervall * 3)}s,state=OFF"})
        self.melde_alles()

    # --- States melden ---------------------------------------------------------------
    def melde_alles(self) -> None:
        self.items.postUpdate(LUEFTER, "ON" if self.luefter_an else "OFF")
        self.messen_und_melden()

    def messen_und_melden(self) -> None:
        temperatur, feuchte = self.sensor.messen(self.luefter_an)
        self.items.postUpdate(TEMP, f"{temperatur} °C")
        self.items.postUpdate(FEUCHTE, f"{feuchte} %")
        jetzt = datetime.now().astimezone().isoformat(timespec="seconds")
        self.items.postUpdate(MELDUNG, jetzt)
        self.items.postUpdate(ONLINE, "ON")                       # Lebenszeichen
        log.info("gemeldet: %.1f °C, %d %%, Lüfter %s", temperatur, feuchte,
                 "an" if self.luefter_an else "aus")
        if temperatur > GRENZE_C and not self.luefter_an:      # lokal entscheiden
            log.warning("zu warm – Lüfter wird lokal eingeschaltet")
            self.schalten(True)

    # --- Commands empfangen ------------------------------------------------------------
    def schalten(self, an: bool) -> None:
        self.luefter_an = an                       # hier säße die echte Hardware
        self.items.postUpdate(LUEFTER, "ON" if an else "OFF")     # Bestätigung als State

    def commands_empfangen(self) -> None:
        while not self.stopp.is_set():
            strom = ItemEvents(self.client).ItemCommandEvent(LUEFTER)
            if isinstance(strom, dict):
                log.warning("kein Ereignisstrom: %s", strom["error"])
                self.stopp.wait(5)
                continue
            log.info("warte auf Commands für %s", LUEFTER)
            self.melde_alles()                     # nach (Wieder-)Verbinden alles melden
            try:
                for e in iterSSEEvents(strom):
                    command = e["payload"]["value"]
                    log.info("Command empfangen: %s <- %s", LUEFTER, command)
                    if command in ("ON", "OFF"):
                        self.schalten(command == "ON")
            except Exception as fehler:
                log.warning("Ereignisstrom unterbrochen: %s", type(fehler).__name__)
            self.stopp.wait(2)

    def laufen(self) -> None:
        threading.Thread(target=self.commands_empfangen, daemon=True).start()
        while not self.stopp.wait(self.intervall):
            self.messen_und_melden()

    def abmelden(self) -> None:
        self.items.postUpdate(ONLINE, "OFF")
        log.info("abgemeldet")


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtuelles Werkstattgerät für openHAB")
    parser.add_argument("--intervall", type=float, default=10, help="Sekunden je Messung")
    parser.add_argument("--dauer", type=float, default=0, help="nach N s beenden (Test)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S",
                        format="%(asctime)s %(levelname)-7s %(message)s")

    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    geraet = WerkstattGeraet(client, args.intervall)
    geraet.anmelden()
    if args.dauer:
        threading.Timer(args.dauer, geraet.stopp.set).start()
    try:
        geraet.laufen()
    except KeyboardInterrupt:
        pass
    geraet.abmelden()


if __name__ == "__main__":
    main()
