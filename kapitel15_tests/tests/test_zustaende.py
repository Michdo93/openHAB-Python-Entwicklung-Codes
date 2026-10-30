"""Unit-Tests: reine Logik, kein openHAB nötig – laufen in Millisekunden."""

import pytest

from buchlib import HSB, Ereignis, als_bool, als_zahl, einheit, parse_zeile


@pytest.mark.parametrize(
    "state, erwartet",
    [
        ("21.5 °C", 21.5),
        ("42", 42.0),
        ("-3.25 °C", -3.25),
        ("NULL", None),
        ("UNDEF", None),
        (None, None),
        ("kaputt", None),
    ],
)
def test_als_zahl(state, erwartet):
    assert als_zahl(state) == erwartet


def test_als_zahl_mit_standard():
    assert als_zahl("NULL", standard=0.0) == 0.0


def test_einheit():
    assert einheit("21.5 °C") == "°C"
    assert einheit("42") == ""


@pytest.mark.parametrize(
    "state, erwartet",
    [
        ("ON", True),
        ("OFF", False),
        ("OPEN", True),
        ("CLOSED", False),
        ("0", False),
        ("35", True),
        ("NULL", None),
    ],
)
def test_als_bool(state, erwartet):
    assert als_bool(state) is erwartet


def test_hsb_hin_und_zurueck():
    farbe = HSB.aus_state("240,100,75")
    assert farbe.farbton == 240 and farbe.helligkeit == 75
    assert farbe.als_command() == "240,100,75"


def test_parse_zeile_entpackt_payload():
    zeile = (
        b'data: {"topic":"openhab/items/Wohnzimmer_Licht/statechanged",'
        b'"payload":"{\\"type\\":\\"OnOff\\",\\"value\\":\\"ON\\",'
        b'\\"oldType\\":\\"OnOff\\",\\"oldValue\\":\\"OFF\\"}",'
        b'"type":"ItemStateChangedEvent"}'
    )
    e = parse_zeile(zeile)
    assert isinstance(e, Ereignis)
    assert (e.name, e.wert, e.alter_wert) == ("Wohnzimmer_Licht", "ON", "OFF")


def test_parse_zeile_ignoriert_steuerzeilen():
    assert parse_zeile(b"event: message") is None
    assert parse_zeile(b"") is None
    assert parse_zeile(b'data: {"type":"ALIVE","interval":10}') == {
        "type": "ALIVE",
        "interval": 10,
    }
