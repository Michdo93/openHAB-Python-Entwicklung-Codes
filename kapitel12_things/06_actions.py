"""Kapitel 12: Thing-Actions – Funktionen eines Bindings direkt aufrufen."""
import os
from datetime import datetime, timedelta

from openhab import OpenHABClient, Actions

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
actions = Actions(client)
SONNE = "astro:sun:zuhause"

angebot = actions.getActions(SONNE, language="de")
for a in angebot:
    eingaben = ", ".join(i["name"] for i in a["inputs"])
    print(f"  {a['actionUid'].split('#')[0]:<26} ({eingaben}) – {a['description']}")

# Die UID enthält einen Hash hinter '#' – wir suchen sie über den Namen
uid = {a["actionUid"].split("#")[0]: a["actionUid"] for a in angebot}

print("\nSonnenhöhe über dem Tag (jetzt und die nächsten Stunden):")
jetzt = datetime.now().astimezone().replace(minute=0, second=0, microsecond=0)
for stunden in range(0, 24, 3):
    zeit = jetzt + timedelta(hours=stunden)
    hoehe = actions.executeAction(SONNE, uid["astro.getElevation"],
                                  {"date": zeit.isoformat()})["result"]
    print(f"  {zeit:%d.%m. %H:%M}  {float(hoehe.split()[0]):6.1f}°")

mittag = jetzt.replace(hour=12)
for monat in (3, 6, 9, 12):
    tag = mittag.replace(month=monat, day=21)
    ergebnis = actions.executeAction(SONNE, uid["astro.getElevation"],
                                     {"date": tag.isoformat()})
    print(f"  21.{monat:02d}. 12:00  {float(ergebnis['result'].split()[0]):6.1f}°")
