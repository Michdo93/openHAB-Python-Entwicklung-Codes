"""Kapitel 16: Ein robuster Ereignis-Listener – Momentaufnahme, Wächter, Backoff.

Die Klasse gehört bewusst in dieses Skript und nicht in eine eigene Bibliothek:
Sie zeigt, wie man aus den Bausteinen von python-openhab-rest-client einen
Dienst baut, der Abbrüche übersteht. Kapitel 17 und 18 kopieren sie.
"""
import logging
import os
import random
import socket
import threading
import time
from typing import Callable

from openhab import OpenHABClient, Events, Items, iterSSEEvents

log = logging.getLogger("listener")


class EreignisListener:
    """Liest den Ereignisstrom in einem Hintergrund-Thread und verbindet neu."""

    def __init__(self, client: OpenHABClient, topics: str,
                 bei_verbindung: Callable[[], None] = None, frist: float = 25.0):
        self.client, self.topics, self.frist = client, topics, frist
        self.bei_verbindung = bei_verbindung       # Momentaufnahme nach (Wieder-)Verbinden
        self.beobachter: list[Callable[[dict], None]] = []
        self.verbunden = threading.Event()
        self._stopp = threading.Event()
        self._strom = None
        self._zuletzt = time.monotonic()

    def anmelden(self, rueckruf: Callable[[dict], None]) -> None:
        self.beobachter.append(rueckruf)

    def starten(self) -> "EreignisListener":
        threading.Thread(target=self._schleife, name="sse", daemon=True).start()
        threading.Thread(target=self._waechter, name="sse-waechter", daemon=True).start()
        return self

    def stoppen(self) -> None:
        self._stopp.set()
        self._abbrechen()

    def _abbrechen(self) -> None:
        """Weckt ein blockierendes Lesen auf: close() allein genügt dafür nicht."""
        strom, self._strom = self._strom, None
        try:
            strom.raw.connection.sock.shutdown(socket.SHUT_RDWR)
        except Exception:                      # schon geschlossen oder kein Strom
            pass

    def _waechter(self) -> None:
        """openHAB schickt alle 10 s ein ALIVE – bleibt es aus, ist die Verbindung tot."""
        while not self._stopp.wait(1):
            if self._strom is not None and time.monotonic() - self._zuletzt > self.frist:
                log.warning("Seit %.0f s keine Nachricht – neu verbinden", self.frist)
                self._abbrechen()

    def _schleife(self) -> None:
        versuch = 0
        while not self._stopp.is_set():
            try:
                strom = Events(self.client).getEvents(self.topics)
                if isinstance(strom, dict):                # Fehlerobjekt der Bibliothek
                    raise ConnectionError(strom["error"])
                self._strom, self._zuletzt, versuch = strom, time.monotonic(), 0
                self.verbunden.set()
                log.info("verbunden (%s)", self.topics)
                if self.bei_verbindung:
                    self.bei_verbindung()
                for ereignis in iterSSEEvents(strom, includeAlive=True):
                    self._zuletzt = time.monotonic()
                    if "topic" not in ereignis:            # ALIVE
                        continue
                    for rueckruf in list(self.beobachter):
                        try:
                            rueckruf(ereignis)
                        except Exception:                  # ein Fehler im Beobachter
                            log.exception("Fehler im Beobachter")   # stoppt nicht alles
                if not self._stopp.is_set():
                    log.warning("Strom vom Server beendet")
            except Exception as fehler:
                if not self._stopp.is_set():
                    log.warning("Strom unterbrochen: %s", type(fehler).__name__)
            self._strom = None
            self.verbunden.clear()
            if self._stopp.is_set():
                break
            pause = min(30, 2 ** versuch) + random.uniform(0, 1)    # Backoff mit Jitter
            versuch += 1
            log.info("neuer Versuch in %.1f s", pause)
            self._stopp.wait(pause)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S",
                        format="%(asctime)s %(levelname)-7s %(message)s")
    client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                           token=os.environ.get("OPENHAB_TOKEN"))
    items = Items(client)
    zustaende: dict[str, str] = {}

    def momentaufnahme() -> None:
        for item in items.getItems(fields="name,state"):
            zustaende[item["name"]] = item["state"]
        log.info("Momentaufnahme: %d Items", len(zustaende))

    def geaendert(e: dict) -> None:
        name = e["topic"].split("/")[2]
        zustaende[name] = e["payload"]["value"]
        log.info("%-22s %s -> %s", name, e["payload"]["oldValue"], e["payload"]["value"])

    listener = EreignisListener(client, "openhab/items/*/statechanged", momentaufnahme)
    listener.anmelden(geaendert)
    listener.starten()
    try:
        threading.Event().wait(float(os.environ.get("DAUER", "0")) or None)
    except KeyboardInterrupt:
        pass
    listener.stoppen()
