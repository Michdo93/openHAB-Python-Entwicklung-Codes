"""Kapitel 16: Ereignisse und Commands nebenläufig mit asyncio."""
import asyncio
import os

from openhab import AsyncOpenHABClient, AsyncItemEvents, AsyncItems, aiterSSEEvents

URL = os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080")
TOKEN = os.environ.get("OPENHAB_TOKEN")


async def beobachten(client: AsyncOpenHABClient, anzahl: int) -> None:
    strom = await AsyncItemEvents(client).ItemStateChangedEvent("Wohnzimmer_Dimmer")
    async for e in aiterSSEEvents(strom):
        print(f"  Ereignis: Wohnzimmer_Dimmer = {e['payload']['value']}")
        anzahl -= 1
        if anzahl == 0:
            strom.close()
            return


async def schalten(client: AsyncOpenHABClient) -> None:
    items = AsyncItems(client)
    for wert in ("20", "40", "60"):
        await asyncio.sleep(0.5)
        print(f"Command Wohnzimmer_Dimmer <- {wert}")
        await items.sendCommand("Wohnzimmer_Dimmer", wert)


async def main() -> None:
    async with AsyncOpenHABClient(URL, token=TOKEN) as client:
        await AsyncItems(client).sendCommand("Wohnzimmer_Dimmer", "0")
        await asyncio.sleep(0.5)                  # Ausgangslage, bevor der Strom öffnet
        await asyncio.wait_for(asyncio.gather(beobachten(client, 3), schalten(client)),
                               timeout=10)


asyncio.run(main())
