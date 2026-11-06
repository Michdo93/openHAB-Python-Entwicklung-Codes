"""Kapitel 15: Sitemaps lesen – die Bedienseiten, die Apps und Basic UI zeigen."""
import os

from openhab import OpenHABClient, Sitemaps

client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
sitemaps = Sitemaps(client)

for s in sitemaps.getSitemaps():
    print(f"Sitemap {s['name']}: {s['label']}")


def zeige(widgets: list, tiefe: int = 1) -> None:
    for w in widgets:
        item = w.get("item", {})
        wert = f"= {item['state']}" if item else ""
        print(f"{'  ' * tiefe}{w['type']:<12} {w['label']:<28} {wert}")
        zeige(w.get("widgets", []), tiefe + 1)


seite = sitemaps.getSitemap("restbuch", language="de")["homepage"]
print(f"\nStartseite »{seite['title']}«:")
zeige(seite["widgets"])
