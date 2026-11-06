"""
Kapitel 20: Web-Dashboard mit Flask als Vermittler (Backend for Frontend).

Der Browser spricht NUR mit diesem Server – nie direkt mit openHAB:
  * kein CORS-Problem, das API-Token bleibt auf dem Server,
  * ein einziger State-Tracker-Strom zu openHAB, beliebig viele Browser-Tabs,
  * eine Positivliste legt fest, welche Items bedient werden dürfen,
  * Szenen sind openHAB-Regeln, die der Server per runNow auslöst.

Start:  flask --app kapitel20_projekte/dashboard/app.py run --port 5000
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time

from flask import Flask, Response, abort, jsonify, render_template, request
from openhab import OpenHABClient, Events, Items, Rules, iterSSELines, parseSSEData

ERLAUBT = ["Wohnzimmer_Licht", "Wohnzimmer_Dimmer", "Wohnzimmer_Temperatur",
           "Kueche_Rollladen", "Flur_Haustuer", "Werkstatt_Temperatur",
           "Werkstatt_Luefter", "Haus_Status"]
SZENEN = {"gute-nacht": "restbuch-1"}

app = Flask(__name__)
client = OpenHABClient(os.environ.get("OPENHAB_URL", "http://127.0.0.1:8080"),
                       token=os.environ.get("OPENHAB_TOKEN"))
items, rules, events = Items(client), Rules(client), Events(client)
zustaende: dict[str, dict] = {}
browser: list[queue.Queue] = []
lock = threading.Lock()


def verteilen(name: str, anzeige: str) -> None:
    zustaende[name]["anzeige"] = anzeige
    nachricht = json.dumps({"name": name, "anzeige": anzeige}, ensure_ascii=False)
    with lock:
        for q in browser:
            q.put(nachricht)


def state_tracker() -> None:
    """Hintergrund: der State-Tracker liefert nur unsere Items – fertig formatiert."""
    while True:
        for item in items.getItems(fields="name,label,type,state"):       # Momentaufnahme
            if item["name"] in ERLAUBT:
                zustaende[item["name"]] = {**item, "anzeige": item["state"]}
        strom = events.initiateStateTracker()
        if isinstance(strom, dict):
            time.sleep(5)
            continue
        try:
            for zeile in iterSSELines(strom):
                if not zeile.startswith("data:"):
                    continue
                daten = parseSSEData(zeile)
                if daten is None:                     # 1. Nachricht: Verbindungskennung
                    events.updateSSEConnectionItems(zeile[5:].strip(), ERLAUBT)
                elif "type" not in daten:             # {Itemname: {state, displayState}}
                    for name, z in daten.items():
                        zustaende[name]["state"] = z["state"]
                        verteilen(name, z.get("displayState", z["state"]))
        except Exception:
            time.sleep(2)                             # neu verbinden


threading.Thread(target=state_tracker, daemon=True).start()


@app.get("/")
def index():
    return render_template("index.html", szenen=SZENEN)


@app.get("/api/items")
def api_items():
    return jsonify([zustaende[n] for n in ERLAUBT if n in zustaende])


@app.post("/api/items/<name>")
def api_command(name):
    if name not in ERLAUBT:
        abort(403)
    antwort = items.sendCommand(name, request.get_data(as_text=True), source="dashboard")
    return jsonify(antwort), (400 if "error" in antwort else 200)


@app.post("/api/szenen/<szene>")
def api_szene(szene):
    if szene not in SZENEN:
        abort(404)
    return jsonify(rules.runNow(SZENEN[szene]))


@app.get("/api/stream")
def api_stream():
    q: queue.Queue = queue.Queue()
    with lock:
        browser.append(q)

    def erzeugen():
        try:
            while True:
                try:
                    yield f"data: {q.get(timeout=15)}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        finally:
            with lock:
                browser.remove(q)

    return Response(erzeugen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache"})
