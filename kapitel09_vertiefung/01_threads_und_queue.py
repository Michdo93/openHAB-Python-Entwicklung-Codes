"""Kapitel 9: Threads, Warteschlangen und Logging.

Ein Erzeuger-Thread simuliert eingehende Ereignisse (wie ein SSE-Strom),
der Hauptthread verarbeitet sie. Die Queue entkoppelt beide sicher.
"""

import logging
import queue
import random
import threading
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(threadName)-10s %(levelname)-7s %(message)s",
)
log = logging.getLogger("demo")

ereignisse: "queue.Queue[tuple[str, str]]" = queue.Queue()
stopp = threading.Event()


def erzeuger() -> None:
    """Läuft im Hintergrund und legt Ereignisse in die Queue."""
    while not stopp.is_set():
        wert = f"{random.uniform(19, 23):.1f} °C"
        ereignisse.put(("Wohnzimmer_Temperatur", wert))
        log.debug("erzeugt %s", wert)
        stopp.wait(0.3)


threading.Thread(target=erzeuger, name="Erzeuger", daemon=True).start()

ende = time.monotonic() + 2
while time.monotonic() < ende:
    try:
        name, wert = ereignisse.get(timeout=1)
    except queue.Empty:
        continue
    log.info("%s = %s", name, wert)

stopp.set()
log.info("fertig")
