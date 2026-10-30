#!/usr/bin/env python3
"""
Mock-openHAB – ein kleiner Nachbau der openHAB REST API für Übung und Tests.

Er liest die Übungs-Items aus openhab-conf/items/restbuch.items und bildet
die für das Buch wichtigen Endpunkte nach:

  * /rest, /rest/items (CRUD, Commands, States, Tags, Gruppen)
  * /rest/events (Server-Sent Events mit Topic-Filter, ALIVE-Nachrichten,
    Ereigniskette command -> state -> stateupdated -> statechanged)
  * /rest/things, /rest/rules (runnow, enable), /rest/persistence,
    /rest/sitemaps, /rest/links, /rest/systeminfo

Er ersetzt KEIN echtes openHAB: Es gibt keine Bindings, keine Regel-Engine
und keine Benutzerverwaltung. Anmeldedaten werden angenommen, aber nicht
geprüft. Für die Beispiele und automatisierten Tests des Buchs reicht das.

Start:   python mock/mock_openhab.py            (Port 8080)
         python mock/mock_openhab.py --port 8090
"""
from __future__ import annotations

import argparse
import json
import queue
import random
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request

ITEMS_FILE = Path(__file__).resolve().parent.parent / "openhab-conf" / "items" / "restbuch.items"
ALIVE_INTERVAL = 10

app = Flask(__name__)
lock = threading.RLock()
items: dict[str, dict] = {}
subscribers: list[tuple[re.Pattern, queue.Queue]] = []
history: dict[str, dict[str, list[tuple[int, str]]]] = {"rrd4j": {}, "inmemory": {}}

# --------------------------------------------------------------------------
# Items laden
# --------------------------------------------------------------------------
LINE_RE = re.compile(
    r'^(?P<type>[A-Za-z]+(?::[A-Za-z]+)*(?:\([^)]*\))?)\s+(?P<name>\w+)'
    r'(?:\s+"(?P<label>[^"]*)")?'
    r'(?:\s+<(?P<icon>[^>]+)>)?'
    r'(?:\s+\((?P<groups>[^)]*)\))?'
    r'(?:\s+\[(?P<tags>[^\]]*)\])?')


def load_items(path: Path = ITEMS_FILE) -> None:
    """Liest eine .items-Datei in einfacher openHAB-Syntax ein."""
    with lock:
        items.clear()
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            m = LINE_RE.match(line)
            if not m:
                continue
            full_type = m["type"]
            base = full_type.split(":")[0]
            item_type = full_type if base != "Group" else "Group"
            group_type = None
            function = None
            if base == "Group" and ":" in full_type:
                parts = full_type.split(":")
                group_type = parts[1]
                if len(parts) > 2:
                    function = parts[2]
            label = (m["label"] or "").split("[")[0].strip()
            items[m["name"]] = {
                "name": m["name"],
                "type": item_type,
                "groupType": group_type,
                "function": function,
                "label": label,
                "category": m["icon"] or "",
                "tags": [t.strip().strip('"') for t in (m["tags"] or "").split(",") if t.strip()],
                "groupNames": [g.strip() for g in (m["groups"] or "").split(",") if g.strip()],
                "state": "NULL",
                "editable": False,
                "autoupdate": 'autoupdate="false"' not in line,
            }
        # Startwerte wie die Regel »Startwerte« (restbuch-2) in restbuch.rules
        start = {
            "Wohnzimmer_Temperatur": "21.5 °C", "Kueche_Rollladen": "0",
            "Flur_Haustuer": "CLOSED", "Haus_Status": "Alle zu Hause",
            "Werkstatt_Luefter": "OFF",
        }
        for name, state in start.items():
            if name in items:
                items[name]["state"] = state
        _update_groups()


def _members(group: str) -> list[dict]:
    return [i for i in items.values() if group in i["groupNames"]]


def _update_groups() -> None:
    for g in items.values():
        if g["type"] != "Group" or g["groupType"] != "Switch":
            continue
        states = [m["state"] for m in _members(g["name"])]
        on = sum(1 for s in states if s == "ON" or (s.replace(".", "").isdigit() and float(s) > 0))
        g["state"] = "ON" if on else "OFF"


# --------------------------------------------------------------------------
# Typen und Zustandslogik
# --------------------------------------------------------------------------
def _base(item: dict) -> str:
    t = item["groupType"] if item["type"] == "Group" and item["groupType"] else item["type"]
    return t.split(":")[0]


def _event_type(item: dict, value: str) -> str:
    base = _base(item)
    if value in ("NULL", "UNDEF"):
        return "UnDef"
    if value in ("ON", "OFF"):
        return "OnOff"
    if value in ("OPEN", "CLOSED"):
        return "OpenClosed"
    if value in ("UP", "DOWN"):
        return "UpDown"
    if value in ("INCREASE", "DECREASE"):
        return "IncreaseDecrease"
    if value in ("STOP", "MOVE"):
        return "StopMove"
    return {"Dimmer": "Percent", "Rollershutter": "Percent", "Color": "HSB",
            "String": "String", "DateTime": "DateTime", "Location": "Point",
            "Player": "PlayPause"}.get(base, "Quantity" if " " in value else "Decimal")


def _unit(item: dict) -> str:
    t = item["type"]
    if t == "Number:Temperature":
        return " °C"
    if t == "Number:Dimensionless":
        return " %"
    return ""


def _normalize_state(item: dict, value: str) -> str:
    base = _base(item)
    value = value.strip()
    if value in ("NULL", "UNDEF"):
        return value
    if base == "Number":
        number = value.split(" ")[0]
        float(number)                                    # wirft bei Unsinn
        return f"{number}{_unit(item)}"
    if base in ("Dimmer", "Rollershutter"):
        v = float(value)
        if not 0 <= v <= 100:
            raise ValueError("percent out of range")
        return str(int(v)) if v.is_integer() else str(v)
    if base == "Switch" and value not in ("ON", "OFF"):
        raise ValueError("invalid switch state")
    if base == "Contact" and value not in ("OPEN", "CLOSED"):
        raise ValueError("invalid contact state")
    return value


def _apply_command(item: dict, cmd: str) -> str | None:
    """Liefert den durch autoupdate vorhergesagten State oder None."""
    base = _base(item)
    cur = item["state"]
    cmd = cmd.strip()
    if base == "Switch":
        if cmd not in ("ON", "OFF"):
            raise ValueError
        return cmd
    if base == "Dimmer":
        if cmd == "ON":
            return "100"
        if cmd == "OFF":
            return "0"
        if cmd in ("INCREASE", "DECREASE"):
            return None  # wie openHAB ohne Gerät: relative Befehle ändern nichts
        return _normalize_state(item, cmd)
    if base == "Rollershutter":
        if cmd == "UP":
            return "0"
        if cmd == "DOWN":
            return "100"
        if cmd in ("STOP", "MOVE"):
            return None
        return _normalize_state(item, cmd)
    if base == "Color":
        h, s, b = (cur.split(",") + ["0", "0", "0"])[:3] if cur not in ("NULL", "UNDEF") else ("0", "0", "0")
        if cmd == "ON":
            return f"{h},{s},100"
        if cmd == "OFF":
            return f"{h},{s},0"
        if "," in cmd:
            return cmd
        float(cmd)
        return f"{h},{s},{cmd}"
    if base == "Contact":
        raise ValueError("Contact accepts no commands")
    return _normalize_state(item, cmd)


# --------------------------------------------------------------------------
# Ereignisse
# --------------------------------------------------------------------------
def _topic_regex(topics: str | None) -> re.Pattern:
    if not topics:
        return re.compile(r".*")
    parts = [re.escape(t.strip()).replace(r"\*", ".*") for t in topics.split(",") if t.strip()]
    return re.compile("^(" + "|".join(parts) + ")$")


def publish(topic: str, ev_type: str, payload: dict, source: str | None = None) -> None:
    event = {"topic": topic, "payload": json.dumps(payload, ensure_ascii=False), "type": ev_type}
    if source:
        event["source"] = source
    with lock:
        targets = [q for rx, q in subscribers if rx.match(topic)]
    for q in targets:
        q.put(event)


def _set_state(item: dict, new: str, source: str | None = None) -> None:
    old = item["state"]
    item["state"] = new
    name = item["name"]
    stamp = datetime.now().astimezone().isoformat()
    publish(f"openhab/items/{name}/state", "ItemStateEvent",
            {"type": _event_type(item, new), "value": new}, source)
    publish(f"openhab/items/{name}/stateupdated", "ItemStateUpdatedEvent",
            {"type": _event_type(item, new), "value": new, "lastStateUpdate": stamp}, source)
    if old != new:
        publish(f"openhab/items/{name}/statechanged", "ItemStateChangedEvent",
                {"type": _event_type(item, new), "value": new,
                 "oldType": _event_type(item, old), "oldValue": old,
                 "lastStateUpdate": stamp, "lastStateChange": stamp}, source)
        if _base(item) in ("Number", "Switch", "Dimmer", "Rollershutter", "Contact"):
            history["rrd4j"].setdefault(name, []).append((int(time.time() * 1000), new.split(" ")[0]))
    # Gruppen nachziehen
    for g in item["groupNames"]:
        grp = items.get(g)
        if grp and grp["groupType"] == "Switch":
            before = grp["state"]
            _update_groups()
            if grp["state"] != before:
                publish(f"openhab/items/{g}/{name}/statechanged", "GroupItemStateChangedEvent",
                        {"type": "OnOff", "value": grp["state"], "oldType": "OnOff", "oldValue": before})


def send_command(name: str, cmd: str) -> None:
    item = items[name]
    if item["type"] == "Group":
        publish(f"openhab/items/{name}/command", "ItemCommandEvent",
                {"type": _event_type(item, cmd), "value": cmd}, "org.openhab.core.io.rest")
        for m in _members(name):
            if _base(m) != "Contact":
                try:
                    send_command(m["name"], cmd)
                except ValueError:
                    pass
        return
    predicted = _apply_command(item, cmd)
    publish(f"openhab/items/{name}/command", "ItemCommandEvent",
            {"type": _event_type(item, cmd), "value": cmd}, "org.openhab.core.io.rest")
    # Wie openHAB bei Items ohne Channel-Link: autoupdate setzt den Zustand direkt
    # (ein ItemStatePredictedEvent gibt es nur bei verlinkten Items).
    if predicted is not None and item.get("autoupdate", True):
        _set_state(item, predicted)


# --------------------------------------------------------------------------
# REST-Endpunkte: Wurzel, Items
# --------------------------------------------------------------------------
def _item_json(item: dict, recursive: bool = False) -> dict:
    base = request.host_url.rstrip("/")
    data = {k: v for k, v in item.items() if k not in ("groupType", "function") and v is not None}
    data["link"] = f"{base}/rest/items/{item['name']}"
    if item["type"] == "Group":
        if item["groupType"]:
            data["groupType"] = item["groupType"]
        if recursive:
            data["members"] = [_item_json(m, True) for m in _members(item["name"])]
    return data


@app.get("/rest")
@app.get("/rest/")
def root():
    base = request.host_url.rstrip("/")
    return jsonify({"version": "8", "locale": "de_DE", "measurementSystem": "SI",
                    "runtimeInfo": {"version": "5.x (Mock)", "buildString": "Mock-openHAB"},
                    "links": [{"type": t, "url": f"{base}/rest/{t}"} for t in
                              ("items", "things", "rules", "events", "persistence", "sitemaps",
                               "links", "systeminfo")]})


@app.get("/rest/items")
def get_items():
    with lock:
        result = list(items.values())
        if request.args.get("type"):
            result = [i for i in result if _base(i) == request.args["type"] or i["type"] == request.args["type"]]
        if request.args.get("tags"):
            wanted = set(request.args["tags"].split(","))
            result = [i for i in result if wanted & set(i["tags"])]
        recursive = request.args.get("recursive", "false").lower() == "true"
        data = [_item_json(i, recursive) for i in result]
    if request.args.get("fields"):
        fields = request.args["fields"].split(",")
        data = [{k: v for k, v in d.items() if k in fields} for d in data]
    return jsonify(data)


@app.get("/rest/items/<name>")
def get_item(name):
    with lock:
        if name not in items:
            return jsonify({"error": {"message": f"Item {name} does not exist!", "http-code": 404}}), 404
        return jsonify(_item_json(items[name], request.args.get("recursive", "true").lower() == "true"))


@app.get("/rest/items/<name>/state")
def get_state(name):
    with lock:
        if name not in items:
            return Response("", 404)
        return Response(items[name]["state"], 200, mimetype="text/plain")


@app.post("/rest/items/<name>")
def post_command(name):
    cmd = request.get_data(as_text=True)
    with lock:
        if name not in items:
            return Response("", 404)
        if not cmd:
            return Response("", 400)
        if request.content_type and "text/plain" not in request.content_type:
            return Response("", 415)
        try:
            send_command(name, cmd)
        except (ValueError, KeyError):
            return Response("", 400)
    return Response("", 200)


@app.put("/rest/items/<name>/state")
def put_state(name):
    value = request.get_data(as_text=True)
    with lock:
        if name not in items:
            return Response("", 404)
        try:
            new = _normalize_state(items[name], value)
        except (ValueError, KeyError):
            return Response("", 400)
        _set_state(items[name], new)
    return Response("", 202)


@app.put("/rest/items/<name>")
def put_item(name):
    try:
        data = json.loads(request.get_data(as_text=True))
    except json.JSONDecodeError:
        return Response("", 400)
    with lock:
        if name in items and not items[name].get("editable", True):
            return Response("", 405)
        created = name not in items
        items[name] = {
            "name": name, "type": data.get("type", "String"), "groupType": data.get("groupType"),
            "function": None, "label": data.get("label", ""), "category": data.get("category", ""),
            "tags": data.get("tags", []), "groupNames": data.get("groupNames", []),
            "state": items.get(name, {}).get("state", "NULL"), "editable": True,
        }
        publish(f"openhab/items/{name}/{'added' if created else 'updated'}",
                "ItemAddedEvent" if created else "ItemUpdatedEvent", _item_json(items[name]))
        return jsonify(_item_json(items[name])), (201 if created else 200)


@app.delete("/rest/items/<name>")
def delete_item(name):
    with lock:
        if name not in items:
            return Response("", 404)
        if not items[name].get("editable", True):
            return Response("", 405)
        removed = items.pop(name)
        publish(f"openhab/items/{name}/removed", "ItemRemovedEvent", {"name": removed["name"]})
    return Response("", 200)


@app.put("/rest/items/<name>/tags/<tag>")
def add_tag(name, tag):
    with lock:
        if name not in items:
            return Response("", 404)
        if tag not in items[name]["tags"]:
            items[name]["tags"].append(tag)
    return Response("", 200)


@app.delete("/rest/items/<name>/tags/<tag>")
def remove_tag(name, tag):
    with lock:
        if name not in items:
            return Response("", 404)
        items[name]["tags"] = [t for t in items[name]["tags"] if t != tag]
    return Response("", 200)


@app.put("/rest/items/<group>/members/<name>")
def add_member(group, name):
    with lock:
        if group not in items or name not in items:
            return Response("", 404)
        if name not in items[name]["groupNames"]:
            items[name]["groupNames"].append(group)
    return Response("", 200)


@app.put("/rest/items/<name>/metadata/<ns>")
def add_metadata(name, ns):
    with lock:
        if name not in items:
            return Response("", 404)
        items[name].setdefault("metadata", {})[ns] = json.loads(request.get_data(as_text=True) or "{}")
    return Response("", 200)


# --------------------------------------------------------------------------
# Ereignisstrom
# --------------------------------------------------------------------------
@app.get("/rest/events")
def events():
    rx = _topic_regex(request.args.get("topics"))
    q: queue.Queue = queue.Queue()
    with lock:
        subscribers.append((rx, q))

    def stream():
        try:
            yield ": Mock-openHAB event stream\n\n"
            while True:
                try:
                    ev = q.get(timeout=ALIVE_INTERVAL)
                    yield "event: message\ndata: " + json.dumps(ev, ensure_ascii=False) + "\n\n"
                except queue.Empty:
                    yield "event: alive\ndata: " + json.dumps({"type": "ALIVE", "interval": ALIVE_INTERVAL}) + "\n\n"
        finally:
            with lock:
                if (rx, q) in subscribers:
                    subscribers.remove((rx, q))

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# --------------------------------------------------------------------------
# Things, Regeln, Persistenz, Sitemaps, Links, Systeminfo
# --------------------------------------------------------------------------
THINGS = {
    "hue:bridge:bridge": {"label": "Hue Bridge", "status": "OFFLINE", "detail": "CONFIGURATION_ERROR"},
    "mqtt:broker:mosquitto": {"label": "Mosquitto", "status": "ONLINE"},
    "hue:0210:bridge:3": {"label": "Farblampe Wohnzimmer", "status": "OFFLINE", "detail": "BRIDGE_OFFLINE"},
    "mqtt:topic:mosquitto:werkstatt": {"label": "Werkstatt-Sensor", "status": "ONLINE"},
    "astro:sun:zuhause": {"label": "Sonnendaten", "status": "ONLINE"},
}
RULES = {
    "restbuch-1": {"name": "Gute Nacht", "enabled": True},
    "restbuch-2": {"name": "Startwerte", "enabled": True},
}


def _thing_json(uid: str) -> dict:
    t = THINGS[uid]
    return {"UID": uid, "label": t["label"], "thingTypeUID": ":".join(uid.split(":")[:2]),
            "statusInfo": {"status": t["status"], "statusDetail": t.get("detail", "NONE")},
            "channels": [], "configuration": {}, "properties": {}, "editable": False}


@app.get("/rest/things")
def get_things():
    return jsonify([_thing_json(u) for u in THINGS])


@app.get("/rest/things/<uid>")
def get_thing(uid):
    if uid not in THINGS:
        return Response("", 404)
    return jsonify(_thing_json(uid))


@app.get("/rest/things/<uid>/status")
def get_thing_status(uid):
    if uid not in THINGS:
        return Response("", 404)
    return jsonify(_thing_json(uid)["statusInfo"])


@app.put("/rest/things/<uid>/enable")
def enable_thing(uid):
    if uid not in THINGS:
        return Response("", 404)
    enabled = request.get_data(as_text=True).strip().lower() == "true"
    THINGS[uid]["status"] = "ONLINE" if enabled else "UNINITIALIZED"
    THINGS[uid]["detail"] = "NONE" if enabled else "DISABLED"
    publish(f"openhab/things/{uid}/statuschanged", "ThingStatusInfoChangedEvent",
            [{"status": THINGS[uid]["status"], "statusDetail": THINGS[uid]["detail"]}, {}])
    return jsonify(_thing_json(uid))


def _rule_json(uid: str) -> dict:
    r = RULES[uid]
    status = {"status": "IDLE", "statusDetail": "NONE"} if r["enabled"] else \
             {"status": "UNINITIALIZED", "statusDetail": "DISABLED"}
    return {"uid": uid, "name": r["name"], "status": status, "triggers": [], "conditions": [],
            "actions": [], "configuration": {}, "tags": [], "visibility": "VISIBLE", "editable": False}


@app.get("/rest/rules")
def get_rules():
    return jsonify([_rule_json(u) for u in RULES])


@app.get("/rest/rules/<uid>")
def get_rule(uid):
    if uid not in RULES:
        return Response("", 404)
    return jsonify(_rule_json(uid))


@app.post("/rest/rules/<uid>/enable")
def enable_rule(uid):
    if uid not in RULES:
        return Response("", 404)
    RULES[uid]["enabled"] = request.get_data(as_text=True).strip().lower() == "true"
    return Response("", 200)


@app.post("/rest/rules/<uid>/runnow")
def run_rule(uid):
    if uid not in RULES:
        return Response("", 404)
    if uid == "restbuch-1":                         # »Gute Nacht«
        with lock:
            send_command("gLichter", "OFF")
            _set_state(items["Haus_Status"], "Nachtruhe")
    return Response("", 200)


def _oh_error(code: int, message: str):
    return jsonify({"error": {"message": message, "http-code": code}}), code


@app.get("/rest/persistence")
def get_persistence_services():
    return jsonify([{"id": "inmemory", "label": "In Memory", "type": "Modifiable"},
                    {"id": "rrd4j", "label": "RRD4j", "type": "Queryable"}])


@app.get("/rest/persistence/items")
def get_persisted_items():
    service = request.args.get("serviceId", "rrd4j")
    if service not in history:
        return _oh_error(404, f"Persistence service not found: {service}")
    if service == "rrd4j":
        return _oh_error(405, f"Not supported for persistence service: {service}")
    return jsonify([{"name": n, "count": len(v)} for n, v in history[service].items()])


def _parse_time(value: str | None, default: datetime) -> datetime:
    if not value:
        return default
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return default


@app.get("/rest/persistence/items/<name>")
def get_history(name):
    service = request.args.get("serviceId", "rrd4j")
    if name not in items or service not in history:
        return Response("", 404)
    now = datetime.now(timezone.utc)
    start = _parse_time(request.args.get("starttime"), now - timedelta(days=1))
    end = _parse_time(request.args.get("endtime"), now)
    lo, hi = start.timestamp() * 1000, end.timestamp() * 1000
    data = [{"time": t, "state": s} for t, s in sorted(history[service].get(name, [])) if lo <= t <= hi]
    return jsonify({"name": name, "datapoints": str(len(data)), "data": data})


@app.put("/rest/persistence/items/<name>")
def store_history(name):
    service = request.args.get("serviceId", "rrd4j")
    if name not in items or service not in history:
        return Response("", 404)
    if service == "rrd4j":
        return _oh_error(400, f"Persistence service not modifiable: {service}")
    when = _parse_time(request.args.get("time"), datetime.now(timezone.utc))
    state = (request.args.get("state") or "").split(" ")[0]
    history[service].setdefault(name, []).append((int(when.timestamp() * 1000), state))
    return Response("", 200)


@app.delete("/rest/persistence/items/<name>")
def delete_history(name):
    service = request.args.get("serviceId", "rrd4j")
    if name not in items or service not in history:
        return Response("", 404)
    if service == "rrd4j":
        return _oh_error(400, f"Persistence service not modifiable: {service}")
    now = datetime.now(timezone.utc)
    lo = _parse_time(request.args.get("starttime"), now).timestamp() * 1000
    hi = _parse_time(request.args.get("endtime"), now).timestamp() * 1000
    history[service][name] = [(t, v) for t, v in history[service].get(name, []) if not lo <= t <= hi]
    return Response("", 200)


@app.get("/rest/sitemaps")
def get_sitemaps():
    return jsonify([{"name": "restbuch", "label": "REST-Buch"}])


@app.get("/rest/sitemaps/<name>")
def get_sitemap(name):
    if name != "restbuch":
        return Response("", 404)
    with lock:
        widgets = [{"type": "Switch" if _base(i) == "Switch" else "Text", "label": i["label"],
                    "item": _item_json(i)} for i in items.values() if i["type"] != "Group"]
    return jsonify({"name": "restbuch", "label": "REST-Buch",
                    "homepage": {"id": "restbuch", "widgets": widgets}})


@app.get("/rest/links")
def get_links():
    links = [{"itemName": "Werkstatt_Temperatur",
              "channelUID": "mqtt:topic:mosquitto:werkstatt#temperatur", "configuration": {}}]
    if request.args.get("itemName"):
        links = [lk for lk in links if lk["itemName"] == request.args["itemName"]]
    return jsonify(links)


@app.get("/rest/links/orphans")
def get_orphans():
    return jsonify([])


@app.get("/rest/systeminfo")
def systeminfo():
    return jsonify({"systemInfo": {"configFolder": "/etc/openhab", "userdataFolder": "/var/lib/openhab",
                                   "osName": "Linux", "osVersion": "Ubuntu 26.04 (Mock)", "osArchitecture": "amd64",
                                   "javaVendor": "Mock", "javaVersion": "21", "availableProcessors": 4,
                                   "freeMemory": 0, "totalMemory": 0, "uptime": int(time.monotonic())}})


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock-openHAB für das REST-Buch")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    load_items()
    print(f"Mock-openHAB läuft auf http://{args.host}:{args.port}/rest  (Strg+C beendet)")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
