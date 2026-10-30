"""Unit-Tests für Model und Controller (openHAB als Attrappe)"""

from unittest.mock import MagicMock

from ohapp.controller import Controller
from ohapp.model import ItemModel


class Protokoll:
    """Test-Beobachter, der alle Benachrichtigungen mitschreibt."""

    def __init__(self):
        self.eintraege = []

    def item_geaendert(self, item, alt):
        self.eintraege.append((item.name, alt, item.state))


def test_model_benachrichtigt_nur_bei_aenderung():
    model, protokoll = ItemModel(), Protokoll()
    model.anmelden(protokoll)
    model.setze_zustand("Wohnzimmer_Licht", "ON", typ="Switch")
    model.setze_zustand("Wohnzimmer_Licht", "ON")  # keine Änderung
    model.setze_zustand("Wohnzimmer_Licht", "OFF")
    assert protokoll.eintraege == [
        ("Wohnzimmer_Licht", "NULL", "ON"),
        ("Wohnzimmer_Licht", "ON", "OFF"),
    ]


def test_model_filtert_fremde_items():
    model = ItemModel(["Wohnzimmer_Licht"])
    model.laden(
        [
            {"name": "Wohnzimmer_Licht", "state": "ON"},
            {"name": "Kueche_Rollladen", "state": "0"},
        ]
    )
    assert [i.name for i in model] == ["Wohnzimmer_Licht"]


def test_controller_sendet_command_aendert_aber_model_nicht():
    model = ItemModel()
    model.setze_zustand("Wohnzimmer_Licht", "OFF", typ="Switch")
    items = MagicMock()  # Attrappe statt openHAB
    items.sendCommand.return_value = {"message": "OK"}

    Controller(items, model).umschalten("Wohnzimmer_Licht")

    items.sendCommand.assert_called_once_with("Wohnzimmer_Licht", "ON")
    assert model["Wohnzimmer_Licht"].state == "OFF"  # State-Command-Pattern!
