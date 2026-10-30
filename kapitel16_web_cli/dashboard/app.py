"""
Kapitel 16: Web-Dashboard mit Flask als Vermittler (Backend for Frontend).

Der Browser spricht NUR mit diesem Server – nie direkt mit openHAB:
  * kein CORS-Problem, das API-Token bleibt auf dem Server,
  * ein einziger SSE-Strom zu openHAB, beliebig viele Browser-Tabs,
  * eine Positivliste legt fest, welche Items bedient werden dürfen.

Start:  flask --app kapitel16_web_cli/dashboard/app.py run --port 5000
"""

from __future__ import annotations

import json
import queue
import threading

from flask import Flask, Response, abort, jsonify, render_template, request
from openhab import Items

from buchlib import EreignisListener, create_client

ERLAUBT = [
    "Wohnzimmer_Licht",
    "Wohnzimmer_Dimmer",
    "Wohnzimmer_Temperatur",
    "Kueche_Rollladen",
    "Flur_Haustuer",
    "Werkstatt_Temperatur",
    "Werkstatt_Luefter",
    "Haus_Status",
]

app = Flask(__name__)
client = create_client()
items = Items(client)
zustaende: dict[str, dict] = {}
browser: list[queue.Queue] = []
lock = threading.Lock()


def momentaufnahme() -> None:
    for item in items.getItems(fields="name,label,type,state"):
        if item["name"] in ERLAUBT:
            zustaende[item["name"]] = item


def weiterleiten(e) -> None:
    """SSE von openHAB -> Model -> alle verbundenen Browser."""
    if e.name not in zustaende:
        return
    zustaende[e.name]["state"] = e.wert
    nachricht = json.dumps({"name": e.name, "state": e.wert})
    with lock:
        for q in browser:
            q.put(nachricht)


listener = EreignisListener(
    client, "openhab/items/*/statechanged", bei_verbindung=momentaufnahme
)
listener.anmelden(weiterleiten)
listener.starten()
listener.verbunden.wait(5)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/items")
def api_items():
    return jsonify([zustaende[n] for n in ERLAUBT if n in zustaende])


@app.post("/api/items/<name>")
def api_command(name):
    if name not in ERLAUBT:
        abort(403)
    antwort = items.sendCommand(name, request.get_data(as_text=True))
    return jsonify(antwort), (400 if "error" in antwort else 200)


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

    return Response(
        erzeugen(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
