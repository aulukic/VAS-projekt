import spade
import time
import asyncio
import os
import threading
from dispecer import AgentDispecer
from robot import AgentRobot
from skladiste import SKLADISTE_MAPA

class SharedState:
    """
    Klasa koja služi kao siguran (thread-safe) spremnik za stanje sustava
    koje se dijeli između SPADE agenata i glavne dretve za vizualizaciju.
    """
    def __init__(self):
        self.pozicije_robota = {}
        self.status_poruka = "Sustav pokrenut. Čekaju se zahtjevi robota."
        self._lock = threading.Lock()

    def azuriraj_poziciju_robota(self, robot_jid, pozicija):
        """Ažurira poziciju jednog robota."""
        with self._lock:
            self.pozicije_robota[robot_jid] = pozicija

    def azuriraj_status_poruku(self, poruka):
        """Ažurira zadnju statusnu poruku sustava."""
        with self._lock:
            self.status_poruka = poruka

    def dohvati_stanje_za_prikaz(self):
        """Dohvaća kopiju trenutnih pozicija i statusa za iscrtavanje."""
        with self._lock:
            return self.pozicije_robota.copy(), self.status_poruka

def prikazi_stanje_u_terminalu(mapa_template, shared_state):
    """
    Funkcija koja iscrtava trenutno stanje skladišta u terminalu.
    Briše prethodni prikaz i crta novi na temelju podataka iz SharedState.
    """
    simboli = {0: "·", 1: "█", 2: "S", 3: "P", 4: "D"}
    pozicije_robota, status_poruka = shared_state.dohvati_stanje_za_prikaz()
    temp_mapa = [[simboli.get(celija, "?") for celija in red] for red in mapa_template]

    for robot_jid_str, poz in pozicije_robota.items():
        if 0 <= poz[0] < len(temp_mapa) and 0 <= poz[1] < len(temp_mapa[0]):
            robot_broj = ''.join(filter(str.isdigit, robot_jid_str)) or 'R'
            temp_mapa[poz[0]][poz[1]] = f"\033[91m{robot_broj}\033[0m"

    os.system('cls' if os.name == 'nt' else 'clear')
    print("--- VIŠEAGENTNI SUSTAV ZA KOORDINACIJU ROBOTA ---")
    for red in temp_mapa:
        print(" ".join(red))
    print("-" * (len(mapa_template[0]) * 2 + 1))
    print(f"STATUS: {status_poruka}")
    print("-" * (len(mapa_template[0]) * 2 + 1))
    print("Pritisnite CTRL+C za siguran prekid rada sustava.")

async def main():
    """Glavna funkcija koja inicijalizira i pokreće sustav."""
    shared_state = SharedState()
    agenti = []

    dispecer_jid = "dispecer@localhost"
    dispecer_pass = "tajna"
    pozicije_robota = [(8, 1), (1, 1)]

    dispecer_agent = AgentDispecer(dispecer_jid, dispecer_pass, shared_state)
    await dispecer_agent.start(auto_register=True)
    agenti.append(dispecer_agent)

    for i, pozicija in enumerate(pozicije_robota, 1):
        robot_jid = f"robot{i}@localhost"
        robot_pass = "tajna"
        robot_agent = AgentRobot(robot_jid, robot_pass, dispecer_jid, pozicija, shared_state)
        await robot_agent.start(auto_register=True)
        agenti.append(robot_agent)
        await asyncio.sleep(0.1)

    try:
        while any(agent.is_alive() for agent in agenti):
            prikazi_stanje_u_terminalu(SKLADISTE_MAPA, shared_state)
            await asyncio.sleep(0.1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nPrekidam rad sustava...")
    finally:
        for agent in agenti:
            if agent.is_alive():
                await agent.stop()
        print("Svi agenti su sigurno zaustavljeni.")

if __name__ == '__main__':
    spade.run(main())