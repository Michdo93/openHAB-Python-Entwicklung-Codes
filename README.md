# openHAB & Python-Entwicklung – Beispielprogramme zum Buch

Begleit-Repository zum Buch **»openHAB & Python-Entwicklung«** aus der Reihe
**»openHAB REST API«** von Michael Christian Dörflinger.

Alle Programme, die im Buch besprochen werden, liegen hier lauffähig vor –
geordnet nach Kapiteln. Sie verwenden die Bibliotheken
[python-openhab-rest-client](https://github.com/Michdo93/python-openhab-rest-client)
und [openhab-test-suite](https://github.com/Michdo93/openhab-test-suite).

## Schnellstart (Ubuntu 26.04)

```bash
sudo apt install -y python3-venv git
git clone https://github.com/Michdo93/openHAB-Python-Entwicklung-Codes openhab-python-entwicklung
cd openhab-python-entwicklung
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                 # macht das Paket »buchlib« überall importierbar
cp .env.example .env             # URL und API-Token eintragen
```

### Ohne eigenes openHAB: der Mock-Server

```bash
python mock/mock_openhab.py      # simuliert openHAB auf http://127.0.0.1:8080
```

Der Mock liest dieselben Übungs-Items wie das echte openHAB und bildet die
REST API inklusive Server-Sent Events nach. Er ersetzt kein echtes openHAB,
reicht aber für alle Beispiele und automatisierten Tests des Buchs.

### Mit eigenem openHAB: Übungskonfiguration einspielen

```bash
sudo apt install mosquitto
sudo cp openhab-conf/items/*.items      /etc/openhab/items/
sudo cp openhab-conf/things/*.things    /etc/openhab/things/
sudo cp openhab-conf/sitemaps/*.sitemap /etc/openhab/sitemaps/
sudo cp openhab-conf/rules/*.rules      /etc/openhab/rules/
```

Die Übungs-Items sind in **allen Bänden der Reihe identisch**.

## Inhalt

| Ordner | Kapitel | Inhalt |
|---|---|---|
| `openhab-conf/` | 1 | Übungs-Items, Sitemap, Regel »Gute Nacht« |
| `mock/` | 10 | Mock-openHAB (Flask) für Übung und Tests |
| `buchlib/` | 10–17 | Verbindung aus `.env`, Zustands-Helfer, robuster `EreignisListener` |
| `kapitel08_python/` | 8 | Python-Grundlagen mit Smart-Home-Beispielen |
| `kapitel09_vertiefung/` | 9 | Threads, Queues, Logging, asyncio |
| `kapitel10_erste_schritte/` | 10 | Verbinden, Items lesen, Commands, States, Fehler |
| `kapitel11_verwalten/` | 11 | Items-CRUD, Semantik, Things, Regeln, Persistenz |
| `kapitel12_ereignisse/` | 12 | Server-Sent Events roh, Ereigniskette, robuster Listener, asyncio |
| `kapitel13_mvc/ohapp/` | 13 | MVC + Observer + State-Command (Konsole und Tkinter) |
| `kapitel14_diy_geraet/` | 14 | Philosophie 2: eigenes Gerät meldet States, empfängt Commands |
| `kapitel15_tests/` | 15 | pytest, Unit-Tests, Vorab-Tests mit der Test-Suite |
| `kapitel16_web_cli/` | 16 | Flask-Dashboard (Backend for Frontend), CLI `ohcli` |
| `kapitel17_robotik_ki/` | 17 | ROS-2-Brücke, Ausreißererkennung, Werkzeuge für Sprachmodelle |

## Tests

```bash
pytest -v                                  # startet den Mock automatisch
OPENHAB_TEST_URL=http://testhost:8080 OPENHAB_TEST_TOKEN=oh.xxx pytest -v   # gegen eine Testinstanz
```

> **Hinweis:** Integrationstests schalten Items wirklich. Nur gegen eine
> Testinstanz oder den Mock ausführen!

## Hinweis zur Bibliotheksversion

Die Beispiele benötigen `python-openhab-rest-client` ab Version 21.4.0
(u. a. funktionierende asynchrone Ereignisse, SSE mit API-Token und
korrekte Persistenzparameter). Alle Beispiele wurden gegen openHAB 5.2.3
auf Ubuntu getestet.

## openHAB vorbereiten

Neben den Dateien aus `openhab-conf/` (Items, Things, Regeln, Sitemap)
brauchen die Kapitel 11, 15 und 17 einige Add-ons: **Astro Binding**,
**MQTT Binding** (mit `sudo apt install mosquitto` als Broker),
**Hue Binding** (die Lampe bleibt absichtlich offline) sowie die
Persistenzdienste **RRD4j** und **In-Memory**. Installation in der
Main UI unter *Einstellungen → Add-on Store*.

## Lizenz

MIT – siehe `LICENSE`.
