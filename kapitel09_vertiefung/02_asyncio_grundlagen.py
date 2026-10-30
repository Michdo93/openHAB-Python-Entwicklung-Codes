"""Kapitel 9: asyncio – viele Dinge gleichzeitig in einem Thread."""

import asyncio
import random


async def sensor(name: str, intervall: float, ausgabe: asyncio.Queue) -> None:
    """Simulierter Sensor: liefert in festen Abständen Messwerte."""
    for _ in range(3):
        await asyncio.sleep(intervall)  # gibt die Kontrolle ab
        await ausgabe.put((name, round(random.uniform(18, 24), 1)))


async def auswertung(eingang: asyncio.Queue, anzahl: int) -> None:
    for _ in range(anzahl):
        name, wert = await eingang.get()
        print(f"{name:>10}: {wert} °C")


async def main() -> None:
    q: asyncio.Queue = asyncio.Queue()
    # drei Sensoren und eine Auswertung laufen nebenläufig
    async with asyncio.TaskGroup() as gruppe:
        sensoren = (("Wohnzimmer", 0.2), ("Küche", 0.3), ("Werkstatt", 0.5))
        for name, takt in sensoren:
            gruppe.create_task(sensor(name, takt, q))
        gruppe.create_task(auswertung(q, 9))


asyncio.run(main())
