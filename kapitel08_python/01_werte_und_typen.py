"""Kapitel 8: Werte, Typen und Datenstrukturen – am Beispiel eines Smart Homes."""

raum = "Wohnzimmer"                  # str  – Zeichenkette
temperatur = 21.5                    # float – Gleitkommazahl
lampen = 3                           # int  – ganze Zahl
licht_an = True                      # bool – Wahrheitswert
zustand = None                       # None – »noch kein Wert« (wie NULL)

print(f"{raum}: {temperatur:.1f} °C, {lampen} Lampen, Licht an: {licht_an}")

# Listen: geordnet, veränderbar
lichter = ["Wohnzimmer_Licht", "Wohnzimmer_Dimmer"]
lichter.append("Kueche_Licht")
print(lichter[0], len(lichter), lichter[-1])

# Dictionaries: Schlüssel -> Wert (wie ein JSON-Objekt)
item = {"name": "Wohnzimmer_Licht", "type": "Switch", "state": "ON",
        "tags": ["Switch", "Light"]}
print(item["state"], item.get("label", "(kein Label)"))
item["state"] = "OFF"

# Tupel und Mengen
position = (48.06, 8.53)            # unveränderlich
tags = {"Light", "Switch", "Light"}  # Menge: doppelte fallen weg
print(position[0], sorted(tags))

# Typumwandlung – openHAB liefert Zustände immer als Text!
text = "21.5 °C"
wert = float(text.split(" ")[0])
print(wert + 1)
