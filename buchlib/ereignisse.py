"""
Ereignisse aus dem SSE-Strom von openHAB lesen – einfach und robust.

* parse_zeile()        wandelt eine Zeile des Stroms in ein Ereignis um
                       (inklusive des doppelt kodierten »payload«).
* EreignisListener     liest den Strom in einem eigenen Thread, überwacht
                       die ALIVE-Nachrichten, verbindet sich mit
                       exponentiellem Backoff neu und meldet jedes
                       (Wieder-)Verbinden, damit die Anwendung eine
                       Momentaufnahme laden kann.
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from openhab import Events, OpenHABClient, iterSSELines

log = logging.getLogger(__name__)


@dataclass
class Ereignis:
    """Ein Ereignis vom openHAB-Event-Bus."""

    topic: str
    typ: str
    payload: dict | list = field(default_factory=dict)
    quelle: str | None = None

    @property
    def name(self) -> str:
        """Item- bzw. Thing-Name aus dem Topic (openhab/items/<name>/...)."""
        teile = self.topic.split("/")
        return teile[2] if len(teile) > 2 else ""

    @property
    def wert(self) -> str | None:
        """Neuer Wert (value) – bei Commands der Befehl, sonst der Zustand."""
        return self.payload.get("value") if isinstance(self.payload, dict) else None

    @property
    def alter_wert(self) -> str | None:
        return (
            self.payload.get("oldValue") if isinstance(self.payload, dict) else None
        )


def parse_zeile(zeile: bytes | str) -> Ereignis | dict | None:
    """
    Wandelt eine Zeile des Ereignisstroms um.

    Rückgabe: Ereignis für echte Ereignisse, das rohe dict für Steuer-
    nachrichten wie ALIVE, None für Leer-, Kommentar- und event:-Zeilen.
    """
    if isinstance(zeile, bytes):
        zeile = zeile.decode("utf-8", errors="replace")
    if not zeile.startswith("data:"):
        return None
    try:
        daten = json.loads(zeile[5:].strip())
    except json.JSONDecodeError:
        log.warning("Ungültige Ereigniszeile: %s", zeile)
        return None
    if "topic" not in daten:
        return daten  # z. B. {"type": "ALIVE", ...}
    roh = daten.get("payload") or "{}"
    try:
        payload = json.loads(roh)  # JSON im JSON!
    except json.JSONDecodeError:
        payload = {"value": roh}
    return Ereignis(
        daten["topic"], daten.get("type", ""), payload, daten.get("source")
    )


Rueckruf = Callable[[Ereignis], None]


class EreignisListener:
    """Liest den openHAB-Ereignisstrom robust in einem Hintergrund-Thread."""

    def __init__(
        self,
        client: OpenHABClient,
        topics: str = "openhab/items/*/statechanged",
        bei_verbindung: Callable[[], None] | None = None,
        alive_frist: float = 35.0,
        backoff_start: float = 1.0,
        backoff_max: float = 30.0,
    ):
        self.client = client
        self.topics = topics
        self.bei_verbindung = bei_verbindung
        self.alive_frist = alive_frist
        self.backoff_start = backoff_start
        self.backoff_max = backoff_max
        self._beobachter: list[Rueckruf] = []
        self._stopp = threading.Event()
        self._antwort = None
        self._zuletzt = time.monotonic()
        self._thread: threading.Thread | None = None
        self.verbunden = threading.Event()

    # --- Observer-Schnittstelle --------------------------------------------
    def anmelden(self, rueckruf: Rueckruf) -> None:
        self._beobachter.append(rueckruf)

    def abmelden(self, rueckruf: Rueckruf) -> None:
        self._beobachter.remove(rueckruf)

    # --- Lebenszyklus ---------------------------------------------------------
    def starten(self) -> "EreignisListener":
        self._thread = threading.Thread(
            target=self._schleife, name="openhab-sse", daemon=True
        )
        self._thread.start()
        threading.Thread(
            target=self._waechter, name="openhab-sse-waechter", daemon=True
        ).start()
        return self

    def stoppen(self) -> None:
        """Beendet den Listener, ohne auf die nächste Zeile zu warten."""
        self._stopp.set()
        threading.Thread(target=self._schliessen, daemon=True).start()

    def _schliessen(self) -> None:
        antwort, self._antwort = self._antwort, None
        if antwort is not None:
            try:
                antwort.close()
            except Exception:  # noqa: BLE001
                pass

    def _waechter(self) -> None:
        """Schließt die Verbindung, wenn zu lange nichts (auch kein ALIVE) kam."""
        while not self._stopp.wait(1.0):
            if (
                self._antwort is not None
                and time.monotonic() - self._zuletzt > self.alive_frist
            ):
                log.warning(
                    "Keine Nachricht seit %.0f s – neuer Verbindungsaufbau",
                    self.alive_frist,
                )
                self._schliessen()

    def _schleife(self) -> None:
        versuch = 0
        while not self._stopp.is_set():
            try:
                antwort = Events(self.client).getEvents(self.topics)
                if isinstance(antwort, dict):  # Fehlerobjekt der Bibliothek
                    raise ConnectionError(antwort.get("error", antwort))
                antwort.raise_for_status()
                self._antwort, self._zuletzt = antwort, time.monotonic()
                versuch = 0
                self.verbunden.set()
                log.info("Ereignisstrom verbunden (%s)", self.topics)
                if self.bei_verbindung:
                    self.bei_verbindung()  # Momentaufnahme laden
                for zeile in iterSSELines(antwort):
                    self._zuletzt = time.monotonic()
                    if self._stopp.is_set():
                        break
                    ereignis = parse_zeile(zeile)
                    if isinstance(ereignis, Ereignis):
                        for rueckruf in list(self._beobachter):
                            try:
                                rueckruf(ereignis)
                            except Exception:  # noqa: BLE001
                                log.exception("Fehler im Beobachter %r", rueckruf)
            except Exception as fehler:  # noqa: BLE001
                if not self._stopp.is_set():
                    log.warning("Ereignisstrom unterbrochen: %s", fehler)
            finally:
                self.verbunden.clear()
                self._schliessen()
            if self._stopp.is_set():
                break
            wartezeit = min(self.backoff_max, self.backoff_start * 2**versuch)
            wartezeit += random.uniform(0, self.backoff_start)
            versuch += 1
            log.info("Neuer Verbindungsversuch in %.1f s", wartezeit)
            self._stopp.wait(wartezeit)
