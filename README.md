# openHAB & Python-Entwicklung – Beispielprogramme zum Buch

Begleit-Repository zum Buch **»openHAB & Python-Entwicklung«** aus der Reihe
**»openHAB REST API«** von Michael Christian Dörflinger.

Jedes Programm ist ein eigenständiges Beispiel: Es importiert die Bibliotheken
[python-openhab-rest-client](https://github.com/Michdo93/python-openhab-rest-client)
und [openhab-test-suite](https://github.com/Michdo93/openhab-test-suite) direkt und
spricht mit einem **echten openHAB 5** über dessen REST API – ohne Hardware, ohne
MQTT, ohne Zwischenschicht. Alle Beispiele wurden gegen openHAB 5.2.3 getestet.

## Schnellstart (Ubuntu 26.04)

```bash
sudo apt install -y python3-venv git
git clone <URL dieses Repositorys> openhab-python-entwicklung
cd openhab-python-entwicklung
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp openhab.env.example openhab.env     # API-Token eintragen
source openhab.env
python kapitel10_erste_schritte/01_verbinden.py
```

## openHAB vorbereiten

Die Übungsumgebung besteht aus virtuellen Items (ohne Gerät), zwei Regeln, einer
Sitemap, einem Astro-Thing und zwei Persistenzdiensten. Sie ist in allen Bänden
der Reihe identisch.

```bash
sudo cp openhab-conf/items/*.items            /etc/openhab/items/
sudo cp openhab-conf/things/*.things          /etc/openhab/things/
sudo cp openhab-conf/rules/*.rules            /etc/openhab/rules/
sudo cp openhab-conf/sitemaps/*.sitemap       /etc/openhab/sitemaps/
sudo cp openhab-conf/persistence/*.persist    /etc/openhab/persistence/
```

Benötigte Add-ons (Main UI → Einstellungen → Add-on Store): **Astro Binding**,
**RRD4j Persistence**, **InMemory Persistence**. Die MAP-Transformation installiert
Kapitel 14 selbst – per REST.

## Inhalt

| Ordner | Kapitel | Inhalt |
|---|---|---|
| `openhab-conf/` | 1 | Übungs-Items, Regeln, Sitemap, Astro-Thing, Persistenz |
| `kapitel08_python/` | 8 | Python-Grundlagen mit Smart-Home-Beispielen |
| `kapitel09_vertiefung/` | 9 | Threads, Queues, Logging, asyncio |
| `kapitel10_erste_schritte/` | 10 | Verbinden (Token/Basic), Items lesen, Commands, States, Fehler, async |
| `kapitel11_items/` | 11 | Items-CRUD, ganze Räume anlegen, Metadaten, Semantik und Tags, Gruppen |
| `kapitel12_things/` | 12 | Add-ons, Thing-/Channel-Typen, Discovery und Inbox, Things, Links, Actions |
| `kapitel13_regeln/` | 13 | Regeln lesen, anlegen, ändern, ausführen, Zeitpläne, Modultypen |
| `kapitel14_daten/` | 14 | Persistenz lesen, schreiben, löschen; Add-on und Transformation per REST |
| `kapitel15_oberflaechen/` | 15 | Sitemaps lesen, anlegen, live verfolgen; Sprache; Systemdienste |
| `kapitel16_ereignisse/` | 16 | Server-Sent Events, Ereignisarten, State-Tracker, robuster Listener, async |
| `kapitel17_philosophie1/` | 17 | MVC-Anwendung: Commands per REST, States per SSE (Konsole und Tkinter) |
| `kapitel18_philosophie2/` | 18 | Virtuelle Geräte: States per postUpdate, Commands per SSE |
| `kapitel19_tests/` | 19 | pytest, Unit-Tests, Integrationstests und Vorab-Test mit der Test-Suite |
| `kapitel20_projekte/` | 20 | Flask-Dashboard, CLI `ohcli`, Ausreißererkennung, Werkzeuge für Sprachmodelle |

## Tests

```bash
source openhab.env
pytest -v kapitel19_tests          # Integrationstests schalten Items wirklich!
```

Ohne erreichbares openHAB laufen nur die Unit-Tests; die Integrationstests werden
übersprungen.

## Lizenz

MIT – siehe `LICENSE`.
