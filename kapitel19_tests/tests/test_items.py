"""Integrationstests mit dem ItemTester: Existenz, Typ, Gruppen und Verhalten."""
import pytest
from openhab_test_suite import ItemTester

pytestmark = pytest.mark.integration

BENOETIGT = {
    "Wohnzimmer_Licht": "Switch", "Wohnzimmer_Dimmer": "Dimmer",
    "Wohnzimmer_Farblicht": "Color", "Wohnzimmer_Temperatur": "Number:Temperature",
    "Kueche_Rollladen": "Rollershutter", "Flur_Haustuer": "Contact",
    "Haus_Status": "String", "gLichter": "Group",
}


@pytest.fixture(scope="module")
def tester(client):
    return ItemTester(client)


@pytest.mark.parametrize("name, typ", BENOETIGT.items())
def test_item_existiert_mit_typ(tester, name, typ):
    assert tester.doesItemExist(name), f"{name} fehlt"
    assert tester.checkItemIsType(name, typ), f"{name} ist kein {typ}"


def test_lichtgruppe(tester):
    assert tester.isGroupItem("gLichter")
    assert tester.doesGroupContainMember("gLichter", "Wohnzimmer_Licht")
    namen = {m["name"] for m in tester.getGroupMembers("gLichter")}
    assert namen >= {"Wohnzimmer_Licht", "Wohnzimmer_Dimmer"}


def test_schalter(tester):
    assert tester.testSwitch("Wohnzimmer_Licht", "ON", expectedState="ON", timeout=5)


def test_dimmer(tester):
    assert tester.testDimmer("Wohnzimmer_Dimmer", "40", expectedState="40", timeout=5)


def test_farbe(tester):
    assert tester.testColor("Wohnzimmer_Farblicht", "120,100,50",
                            expectedState="120,100,50", timeout=5)


def test_text(tester):
    assert tester.testString("Haus_Status", "Test", expectedState="Test", timeout=5)


def test_kontakt_nur_per_update(tester):
    assert tester.testContact("Flur_Haustuer", update="OPEN", expectedState="OPEN",
                              timeout=5)
