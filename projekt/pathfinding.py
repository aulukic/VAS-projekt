import heapq

class Cvor:
    """
    Klasa koja predstavlja čvor u A* pretrazi. Svaki čvor odgovara
    jednom polju u mreži skladišta i sadrži informacije o svom roditelju
    (prethodnom čvoru na putu) te cijenama kretanja (g, h, f).
    """
    def __init__(self, roditelj=None, pozicija=None):
        self.roditelj = roditelj
        self.pozicija = pozicija

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.pozicija == other.pozicija

    def __lt__(self, other):
        return self.f < other.f

    def __gt__(self, other):
        return self.f > other.f

def astar(mapa, start, cilj):
    """
    Pronalazi najkraći put od startne do ciljne točke na zadanoj mapi
    koristeći A* (A-zvijezda) algoritam pretrage.
    
    Argumenti:
        mapa (list[list]): 2D prikaz skladišta gdje 1 označava prepreku.
        start (tuple): Koordinate (red, stupac) početne točke.
        cilj (tuple): Koordinate (red, stupac) ciljne točke.
        
    Povratna vrijednost:
        list[tuple]: Lista koordinata koja predstavlja putanju od starta do cilja.
                     Vraća None ako putanja ne postoji.
    """
    start_cvor = Cvor(None, start)
    cilj_cvor = Cvor(None, cilj)

    otvorena_lista = []
    zatvorena_lista = set()

    heapq.heappush(otvorena_lista, start_cvor)

    while otvorena_lista:
        trenutni_cvor = heapq.heappop(otvorena_lista)
        zatvorena_lista.add(trenutni_cvor.pozicija)

        if trenutni_cvor == cilj_cvor:
            putanja = []
            trenutni = trenutni_cvor
            while trenutni is not None:
                putanja.append(trenutni.pozicija)
                trenutni = trenutni.roditelj
            return putanja[::-1]

        djeca = []
        for novi_pomak in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            pozicija_susjeda = (trenutni_cvor.pozicija[0] + novi_pomak[0], trenutni_cvor.pozicija[1] + novi_pomak[1])

            if not (0 <= pozicija_susjeda[0] < len(mapa) and 0 <= pozicija_susjeda[1] < len(mapa[0])):
                continue

            if mapa[pozicija_susjeda[0]][pozicija_susjeda[1]] == 1:
                continue
            
            novi_cvor = Cvor(trenutni_cvor, pozicija_susjeda)
            djeca.append(novi_cvor)

        for dijete in djeca:
            if dijete.pozicija in zatvorena_lista:
                continue

            dijete.g = trenutni_cvor.g + 1
            dijete.h = abs(dijete.pozicija[0] - cilj_cvor.pozicija[0]) + abs(dijete.pozicija[1] - cilj_cvor.pozicija[1])
            dijete.f = dijete.g + dijete.h

            if any(otvoreni_cvor for otvoreni_cvor in otvorena_lista if dijete == otvoreni_cvor and dijete.g > otvoreni_cvor.g):
                continue
            
            heapq.heappush(otvorena_lista, dijete)

    return None