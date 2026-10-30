"""Kapitel 8: Verzweigungen, Schleifen und Comprehensions."""

zustaende = {"Wohnzimmer_Licht": "ON", "Wohnzimmer_Dimmer": "40",
             "Kueche_Rollladen": "100", "Flur_Haustuer": "OPEN",
             "Wohnzimmer_Temperatur": "NULL"}

for name, state in zustaende.items():
    if state in ("NULL", "UNDEF"):
        print(f"{name}: unbekannt")
    elif state == "ON":
        print(f"{name}: eingeschaltet")
    elif state.isdigit() and int(state) > 0:
        print(f"{name}: {state} %")
    else:
        print(f"{name}: {state}")

# match/case (ab Python 3.10) – ideal für Befehle
def beschreibe(command: str) -> str:
    match command:
        case "ON" | "OFF":
            return "Schaltbefehl"
        case "UP" | "DOWN" | "STOP":
            return "Rollladenbefehl"
        case "INCREASE" | "DECREASE":
            return "relativer Befehl"
        case _ if command.replace(".", "", 1).isdigit():
            return "Zahlenwert"
        case _:
            return "unbekannt"

print(beschreibe("UP"), beschreibe("42"))

# Comprehensions: Listen und Dictionaries in einer Zeile filtern
bekannt = {n: s for n, s in zustaende.items() if s not in ("NULL", "UNDEF")}
offene = [n for n, s in zustaende.items() if s == "OPEN"]
print(len(bekannt), offene)

# while-Schleife mit break
versuche = 0
while True:
    versuche += 1
    if versuche == 3:
        print("drei Versuche – Abbruch")
        break
