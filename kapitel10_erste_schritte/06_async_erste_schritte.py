"""Kapitel 10: Dieselben Aufrufe asynchron – viele Zustände gleichzeitig lesen."""
import asyncio
import os
import time

from openhab import AsyncOpenHABClient, AsyncItems

URL = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
TOKEN = os.environ.get("OPENHAB_TOKEN")

NAMEN = ["Wohnzimmer_Licht", "Wohnzimmer_Dimmer", "Wohnzimmer_Temperatur",
         "Kueche_Rollladen", "Flur_Haustuer", "Werkstatt_Temperatur", "Haus_Status"]


async def main() -> None:
    async with AsyncOpenHABClient(URL, token=TOKEN) as client:
        items = AsyncItems(client)
        start = time.perf_counter()
        # alle Anfragen gleichzeitig starten und auf alle Antworten warten
        zustaende = await asyncio.gather(*(items.getItemState(n) for n in NAMEN))
        dauer = (time.perf_counter() - start) * 1000
        for name, state in zip(NAMEN, zustaende):
            print(f"{name:<24} {state}")
        print(f"{len(NAMEN)} Zustände in {dauer:.0f} ms")
        print(await items.sendCommand("Wohnzimmer_Licht", "ON"))


asyncio.run(main())
