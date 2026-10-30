"""Kapitel 12: Ereignisse und Commands nebenläufig mit asyncio."""

import asyncio
import json
import os

from openhab import AsyncItemEvents, AsyncItems, AsyncOpenHABClient

URL = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
TOKEN = os.environ.get("OPENHAB_TOKEN") or None


async def beobachten(client: AsyncOpenHABClient, anzahl: int) -> None:
    antwort = await AsyncItemEvents(client).ItemStateChangedEvent(
        "Wohnzimmer_Dimmer"
    )
    async for zeile in antwort.content:  # zeilenweise lesen
        zeile = zeile.decode().strip()
        if not zeile.startswith("data:"):
            continue
        ereignis = json.loads(zeile[5:])
        if "topic" not in ereignis:
            continue
        payload = json.loads(ereignis["payload"])
        print(f"  Ereignis: Wohnzimmer_Dimmer = {payload['value']}")
        anzahl -= 1
        if anzahl == 0:
            antwort.close()
            return


async def schalten(client: AsyncOpenHABClient) -> None:
    items = AsyncItems(client)
    for wert in ("20", "40", "60"):
        await asyncio.sleep(0.5)
        print(f"Command Wohnzimmer_Dimmer <- {wert}")
        await items.sendCommand("Wohnzimmer_Dimmer", wert)


async def main() -> None:
    async with AsyncOpenHABClient(URL, token=TOKEN) as client:
        await asyncio.wait_for(
            asyncio.gather(beobachten(client, 3), schalten(client)), timeout=10
        )


asyncio.run(main())
