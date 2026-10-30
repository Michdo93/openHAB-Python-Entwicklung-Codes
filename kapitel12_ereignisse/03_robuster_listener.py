"""Kapitel 12: Momentaufnahme + robuster Ereignisstrom mit EreignisListener."""

import logging
import signal
import threading

from openhab import Items

from buchlib import create_client, EreignisListener, Ereignis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)

client = create_client()
items = Items(client)
zustaende: dict[str, str] = {}


def momentaufnahme() -> None:
    """Wird nach jedem (Wieder-)Verbinden aufgerufen."""
    for item in items.getItems(fields="name,state"):
        zustaende[item["name"]] = item["state"]
    logging.info("Momentaufnahme: %d Items", len(zustaende))


def bei_ereignis(e: Ereignis) -> None:
    zustaende[e.name] = e.wert
    logging.info("%-24s %s -> %s", e.name, e.alter_wert, e.wert)


listener = EreignisListener(
    client, topics="openhab/items/*/statechanged", bei_verbindung=momentaufnahme
)
listener.anmelden(bei_ereignis)
listener.starten()

ende = threading.Event()
signal.signal(signal.SIGINT, lambda *_: ende.set())
signal.signal(signal.SIGTERM, lambda *_: ende.set())
ende.wait()
listener.stoppen()
