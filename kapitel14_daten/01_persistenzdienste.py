"""Kapitel 14: Persistenzdienste und die Items, die sie speichern."""
import os

from openhab import OpenHABClient, Persistence

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
persistence = Persistence(client)

for dienst in persistence.getServices(language="de"):
    print(f"{dienst['id']:<9} {dienst['type']:<10} {dienst['label']}")

# Was liegt im Arbeitsspeicher-Dienst – und seit wann?
for eintrag in persistence.getItemsFromService("inmemory")[:6]:
    print(f"  {eintrag['name']:<24} {eintrag.get('count', '?'):>4} Werte, "
          f"ältester {eintrag.get('earliest', '–')}")

# rrd4j kann keine Itemliste liefern – die Bibliothek erklärt den Grund
print("rrd4j:", persistence.getItemsFromService("rrd4j"))
