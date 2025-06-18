import numpy as np

# --- Konstante za prikaz elemenata u skladištu ---
PROLAZ = 0
ZID = 1
POLICA = 1
START = 2
LOKACIJA_PAKETA = 3
ODLAGALISTE = 4

# --- Definicija mape skladišta ---
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

# --- Lista zadataka za transport ---
ZADACI = [
    {"uzmi_lokacija": (2, 2), "odnesi_lokacija": (2, 6)},
    {"uzmi_lokacija": (8, 6), "odnesi_lokacija": (1, 9)},
    {"uzmi_lokacija": (7, 2), "odnesi_lokacija": (7, 10)},
    {"uzmi_lokacija": (3, 10), "odnesi_lokacija": (6, 1)},
]
