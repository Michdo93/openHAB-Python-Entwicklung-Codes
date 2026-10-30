"""Kapitel 11: Den Status der Geräte (Things) überwachen."""

from openhab import Things

from buchlib import create_client

things = Things(create_client())

SYMBOL = {"ONLINE": "+", "OFFLINE": "x", "UNKNOWN": "?"}

for thing in things.getThings():
    info = thing["statusInfo"]
    status = info["status"]
    detail = (
        ""
        if info.get("statusDetail") in (None, "NONE")
        else f" ({info['statusDetail']})"
    )
    print(f" {SYMBOL.get(status, '·')} {thing['label']:<24} {status}{detail}")
    print(f"   {thing['UID']}")

offline = [
    t["label"] for t in things.getThings() if t["statusInfo"]["status"] != "ONLINE"
]
if offline:
    print("\nAchtung, nicht erreichbar:", ", ".join(offline))
