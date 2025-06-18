import numpy as np

PROLAZ = 0
ZID = 1
POLICA = 1
START = 2
LOKACIJA_PAKETA = 3
ODLAGAimport numpy as np

# Konstante za prikaz elemenata u skladištu ---
PROLAZ = 0
ZID = 1
POLICA = 1  # Polica je ista kao i zid, neprohodna
START = 2
LOKACIJA_PAKETA = 3
ODLAGALISTE = 4

SKLADISTE_MAPA = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 3, 0, 1, 0, 4, 0, 1, 0, 0, 1], # 3 = LOKACIJA_PAKETA, 4 = ODLAGALISTE
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], # 2 = START (početna pozicija robota)
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
])

# Primjer definiranja lokacija za zadatke
# Ovo će kasnije koristiti AgentDispečer
ZADACI = [
    {"uzmi_lokacija": (2, 2), "odnesi_lokacija": (2, 6)},
    {"uzmi_lokacija": (7, 2), "odnesi_lokacija": (7, 10)},
    {"uzmi_lokacija": (1, 9), "odnesi_lokacija": (8, 6)},
]

def prikazi_skladiste(mapa):
    """Pomoćna funkcija za vizualni prikaz skladišta u konzoli."""
    simboli = {
        PROLAZ: " ",
        ZID: "█",
        START: "S",
        LOKACIJA_PAKETA: "P",
        ODLAGALISTE: "D"
    }
    for red in mapa:
        print("".join([simboli.get(celija, "?") for celija in red]))

if __name__ == '__main__':
    print("Prikaz modela skladišta:")
    prikazi_skladiste(SKLADISTE_MAPA)
    print(f"\nPrimjer prvog zadatka: Uzmi s {ZADACI[0]['uzmi_lokacija']}, odnesi na {ZADACI[0]['odnesi_lokacija']}")LISTE = 4

SKLADISTE_MAPA = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 3, 0, 1, 0, 4, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
])

ZADACI = [
    {"uzmi_lokacija": (2, 2), "odnesi_lokacija": (2, 6)},
    {"uzmi_lokacija": (8, 6), "odnesi_lokacija": (1, 9)},
    {"uzmi_lokacija": (7, 2), "odnesi_lokacija": (7, 10)},
    {"uzmi_lokacija": (3, 10), "odnesi_lokacija": (6, 1)},
]