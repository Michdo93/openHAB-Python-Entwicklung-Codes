"""Kapitel 18: Ein virtueller Rollladenmotor – Commands rein, Position raus.

Ein echter Motor fährt nicht sofort auf 100 %, er braucht Zeit und kann
gestoppt werden. Genau das bildet dieses Programm nach: Es nimmt UP, DOWN,
STOP und Prozentwerte als Commands an und meldet die Position schrittweise.
"""
import argparse
import logging
import os
import threading

from openhab import OpenHABClient, ItemEvents, Items, iterSSEEvents

log = logging.getLogger("motor")
ITEM = "Kueche_Rollladen"


class RollladenMotor:
    def __init__(self, client: OpenHABClient, schritt_s: float = 0.4):
        self.client, self.items, self.schritt_s = client, Items(client), schritt_s
        state = self.items.getItemState(ITEM)
        self.position = int(state) if state.isdigit() else 0     # 0 offen, 100 zu
        self.ziel = self.position
        self.stopp = threading.Event()
        self.bewegt = threading.Event()

    def autoupdate_aus(self) -> None:
        """Nur der Motor bestimmt die Position – openHAB soll nichts vorhersagen."""
        self.items.addMetadata(ITEM, "autoupdate", {"value": "false"})

    def autoupdate_zurueck(self) -> None:
        self.items.removeMetadata(ITEM, "autoupdate")

    def command(self, wert: str) -> None:
        ziele = {"UP": 0, "DOWN": 100, "STOP": self.position}
        self.ziel = ziele[wert] if wert in ziele else max(0, min(100, int(float(wert))))
        log.info("Command %s -> Ziel %d %%", wert, self.ziel)
        self.bewegt.set()

    def fahren(self) -> None:
        """Eigener Thread: fährt in 10-%-Schritten und meldet jede Position."""
        while not self.stopp.is_set():
            self.bewegt.wait(1)
            while self.position != self.ziel and not self.stopp.is_set():
                schritt = 10 if self.ziel > self.position else -10
                self.position = max(0, min(100, self.position + schritt))
                if (schritt > 0 and self.position > self.ziel) or \
                        (schritt < 0 and self.position < self.ziel):
                    self.position = self.ziel
                self.items.postUpdate(ITEM, str(self.position))
                log.info("Position %3d %%", self.position)
                self.stopp.wait(self.schritt_s)
            self.bewegt.clear()

    def laufen(self) -> None:
        threading.Thread(target=self.fahren, daemon=True).start()
        while not self.stopp.is_set():
            strom = ItemEvents(self.client).ItemCommandEvent(ITEM)
            if isinstance(strom, dict):
                self.stopp.wait(5)
                continue
            self.items.postUpdate(ITEM, str(self.position))     # Position melden
            try:
                for e in iterSSEEvents(strom):
                    self.command(e["payload"]["value"])
            except Exception:
                self.stopp.wait(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Virtueller Rollladenmotor")
    parser.add_argument("--dauer", type=float, default=0, help="nach N s beenden (Test)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S",
                        format="%(asctime)s %(levelname)-7s %(message)s")
    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    motor = RollladenMotor(client)
    motor.autoupdate_aus()
    if args.dauer:
        threading.Timer(args.dauer, motor.stopp.set).start()
    threading.Thread(target=motor.laufen, daemon=True).start()
    try:
        motor.stopp.wait()
    except KeyboardInterrupt:
        motor.stopp.set()
    motor.autoupdate_zurueck()


if __name__ == "__main__":
    main()
