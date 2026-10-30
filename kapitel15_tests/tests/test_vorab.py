"""
Integrations- und Vorab-Tests mit der openhab-test-suite.

Sie prüfen genau die Annahmen, auf die sich die Beispielanwendungen
verlassen – bevor ein Roboter losfährt oder ein Dashboard live geht.
Achtung: testSwitch & Co. schalten die Items wirklich (und danach zurück).
"""

import pytest
from openhab_test_suite import ItemTester, RuleTester, SitemapTester, ThingTester

pytestmark = pytest.mark.integration

BENOETIGTE_ITEMS = {
    "Wohnzimmer_Licht": "Switch",
    "Wohnzimmer_Dimmer": "Dimmer",
    "Wohnzimmer_Temperatur": "Number",
    "Kueche_Rollladen": "Rollershutter",
    "Flur_Haustuer": "Contact",
    "Werkstatt_Luefter": "Switch",
    "gLichter": "Group",
}


@pytest.fixture(scope="module")
def item_tester(client):
    return ItemTester(client)


@pytest.mark.parametrize("name, typ", BENOETIGTE_ITEMS.items())
def test_item_existiert_mit_typ(item_tester, name, typ):
    assert item_tester.doesItemExist(name), f"{name} fehlt"
    assert item_tester.checkItemIsType(name, typ), f"{name} ist kein {typ}"


def test_lichtgruppe_enthaelt_deckenlicht(item_tester):
    assert item_tester.doesGroupContainMember("gLichter", "Wohnzimmer_Licht")


def test_schalter_reagiert(item_tester):
    assert item_tester.testSwitch(
        "Wohnzimmer_Licht", "ON", expectedState="ON", timeout=5
    )


def test_dimmer_reagiert(item_tester):
    assert item_tester.testDimmer(
        "Wohnzimmer_Dimmer", "40", expectedState="40", timeout=5
    )


def test_rollladen_reagiert(item_tester):
    assert item_tester.testRollershutter(
        "Kueche_Rollladen", "DOWN", expectedState="100", timeout=5
    )


def test_werkstatt_sensor_online(client):
    assert ThingTester(client).isThingOnline("mqtt:topic:mosquitto:werkstatt")


def test_regel_gute_nacht(client):
    assert RuleTester(client).testRuleExecution(
        "restbuch-1", "Haus_Status", "Nachtruhe"
    )


def test_sitemap_zeigt_luefter(client):
    tester = SitemapTester(client)
    assert tester.doesSitemapExist("restbuch")
    assert tester.doesSitemapContainItem("restbuch", "Werkstatt_Luefter")
