"""
Kapitel 14 – Philosophie 2: Ein selbst gebautes Gerät meldet sich bei openHAB.

Das Gerät (z. B. ein Raspberry Pi in der Werkstatt)
  * misst Temperatur und Feuchte und meldet sie als STATES an openHAB,
  * empfängt COMMANDS für den Lüfter über den Ereignisstrom,
  * schaltet den Lüfter und bestätigt den neuen Zustand mit einem State,
  * schaltet bei Überhitzung selbstständig ein (es ist Eigentümer des Items).

Ohne Hardware läuft es mit simulierten Bausteinen; mit --gpio wird ein
Relais an GPIO 17 über gpiozero geschaltet.
"""

from __future__ import annotations

import argparse
import logging
import random
import signal
import threading
from datetime import datetime

from openhab import Items

from buchlib import Ereignis, EreignisListener, create_client

log = logging.getLogger("werkstatt")

ITEM_TEMP = "Werkstatt_Temperatur"
ITEM_FEUCHTE = "Werkstatt_Feuchte"
ITEM_LUEFTER = "Werkstatt_Luefter"
ITEM_MELDUNG = "Werkstatt_LetzteMeldung"
GRENZE_C = 26.0


# --------------------------------------------------------------------------
# Hardware-Abstraktion: gleiche Schnittstelle für Simulation und echte Teile
# --------------------------------------------------------------------------
class SimulierterSensor:
    def __init__(self) -> None:
        self.temperatur, self.feuchte = 19.0, 55.0

    def messen(self) -> tuple[float, float]:
        self.temperatur += random.uniform(-0.3, 0.4)
        self.feuchte = min(95, max(20, self.feuchte + random.uniform(-1, 1)))
        return round(self.temperatur, 1), round(self.feuchte)


class SimulierterLuefter:
    def __init__(self) -> None:
        self.an = False

    def schalten(self, an: bool) -> None:
        self.an = an
        log.info("Lüfter %s", "EIN" if an else "AUS")


class GpioLuefter(SimulierterLuefter):
    """Relais an einem GPIO-Pin (Raspberry Pi, Paket gpiozero)."""

    def __init__(self, pin: int = 17) -> None:
        super().__init__()
        from gpiozero import OutputDevice  # nur auf dem Pi nötig

        self._relais = OutputDevice(pin, active_high=True, initial_value=False)

    def schalten(self, an: bool) -> None:
        self._relais.on() if an else self._relais.off()
        super().schalten(an)


# --------------------------------------------------------------------------
# Das Gerät
# --------------------------------------------------------------------------
class WerkstattGeraet:
    def __init__(self, items: Items, sensor, luefter, intervall: float):
        self.items, self.sensor, self.luefter = items, sensor, luefter
        self.intervall = intervall
        self.stopp = threading.Event()

    # Commands von openHAB empfangen ----------------------------------------
    def bei_command(self, e: Ereignis) -> None:
        if e.name != ITEM_LUEFTER or e.wert not in ("ON", "OFF"):
            return
        log.info("Command empfangen: %s <- %s", e.name, e.wert)
        self.luefter.schalten(e.wert == "ON")
        self.melde_luefter()  # Bestätigung als State

    # States an openHAB melden ----------------------------------------------
    def melde_luefter(self) -> None:
        self.items.postUpdate(ITEM_LUEFTER, "ON" if self.luefter.an else "OFF")

    def melde_alles(self) -> None:
        """Nach jedem (Wieder-)Verbinden den eigenen Zustand vollständig melden."""
        self.melde_luefter()
        self.messen_und_melden()

    def messen_und_melden(self) -> None:
        temperatur, feuchte = self.sensor.messen()
        self.items.postUpdate(ITEM_TEMP, f"{temperatur} °C")
        self.items.postUpdate(ITEM_FEUCHTE, str(feuchte))
        self.items.postUpdate(
            ITEM_MELDUNG, datetime.now().astimezone().isoformat(timespec="seconds")
        )
        log.info("gemeldet: %.1f °C, %d %%", temperatur, feuchte)
        if temperatur > GRENZE_C and not self.luefter.an:  # lokale Schutzfunktion
            log.warning("Überhitzung – Lüfter wird lokal eingeschaltet")
            self.luefter.schalten(True)
            self.melde_luefter()

    def laufen(self) -> None:
        while not self.stopp.wait(self.intervall):
            try:
                self.messen_und_melden()
            except Exception as fehler:  # noqa: BLE001
                log.warning("Melden fehlgeschlagen: %s", fehler)


def main() -> None:
    parser = argparse.ArgumentParser(description="DIY-Werkstattgerät für openHAB")
    parser.add_argument(
        "--intervall", type=float, default=30, help="Sekunden zwischen Messungen"
    )
    parser.add_argument(
        "--gpio", action="store_true", help="echtes Relais an GPIO 17 schalten"
    )
    parser.add_argument(
        "--dauer", type=float, default=0, help="nach N Sekunden beenden (Test)"
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    client = create_client()
    items = Items(client)
    luefter = GpioLuefter() if args.gpio else SimulierterLuefter()
    geraet = WerkstattGeraet(items, SimulierterSensor(), luefter, args.intervall)

    listener = EreignisListener(
        client,
        topics=f"openhab/items/{ITEM_LUEFTER}/command",
        bei_verbindung=geraet.melde_alles,
    )
    listener.anmelden(geraet.bei_command)
    listener.starten()

    signal.signal(signal.SIGTERM, lambda *_: geraet.stopp.set())
    if args.dauer:
        threading.Timer(args.dauer, geraet.stopp.set).start()
    try:
        geraet.laufen()
    except KeyboardInterrupt:
        pass
    listener.stoppen()
    log.info("beendet")


if __name__ == "__main__":
    main()
