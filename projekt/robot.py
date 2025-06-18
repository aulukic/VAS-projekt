import spade
import json
import asyncio # Potrebno za sleep i druge async operacije
from pathfinding import astar
from skladiste import SKLADISTE_MAPA

# Definicije stanja
ST_CEKANJE_ZADATKA = "ST_CEKANJE_ZADATKA"
ST_KRETANJE_PO_PAKET = "ST_KRETANJE_PO_PAKET"
ST_KRETANJE_DO_ODLAGALISTA = "ST_KRETANJE_DO_ODLAGALISTA"
ST_CEKANJE_NA_PUT = "ST_CEKANJE_NA_PUT"

# --- KLASE PONAŠANJA I STANJA PREMJEŠTENE IZVAN KLASE AGENTA ---

class FSMBehaviour(spade.behaviour.FSMBehaviour):
    """Definira strukturu i tok konačnog automata za robota."""
    async def on_start(self):
        print(f"FSM za {self.agent.jid} pokrenut. Početno stanje: {self.current_state}")

    async def on_end(self):
        print(f"FSM za {self.agent.jid} završen.")
        await self.agent.stop()

class StanjeCekanjaZadatka(spade.behaviour.State):
    """Stanje u kojem robot traži novi zadatak od Dispečera."""
    async def run(self):
        print(f"[{self.agent.jid}] Tražim novi zadatak od dispečera...")
        msg = spade.message.Message(to=self.agent.dispecer_jid)
        msg.set_metadata("performative", "request")
        msg.body = "REQUEST_TASK"
        await self.send(msg)

        reply = await self.receive(timeout=10)
        if reply and reply.metadata.get("performative") == "inform":
            try:
                data = json.loads(reply.body)
                if data.get("status") == "NEMA_ZADATAKA":
                    print(f"[{self.agent.jid}] Nema više zadataka. Čekam.")
                    await asyncio.sleep(5)
                    self.set_next_state(ST_CEKANJE_ZADATKA) # Pokušaj ponovo kasnije
                else:
                    self.agent.trenutni_zadatak = data
                    print(f"[{self.agent.jid}] Dobio zadatak: {self.agent.trenutni_zadatak}")
                    self.set_next_state(ST_KRETANJE_PO_PAKET)
            except json.JSONDecodeError:
                print(f"[{self.agent.jid}] Primio neispravan JSON, čekam...")
                await asyncio.sleep(2)
                self.set_next_state(ST_CEKANJE_ZADATKA)
        else:
            print(f"[{self.agent.jid}] Nema odgovora od dispečera, čekam...")
            await asyncio.sleep(2)
            self.set_next_state(ST_CEKANJE_ZADATKA)

class StanjeKretanja(spade.behaviour.State):
    """
    Stanje koje obuhvaća izračun putanje, zahtjev za rezervaciju i simulaciju
    kretanja do cilja (bilo po paket ili na odlagalište).
    """
    async def run(self):
        current_state_name = self.current_state # Ispravan način dohvaćanja imena stanja
        if current_state_name == ST_KRETANJE_PO_PAKET:
            cilj = tuple(self.agent.trenutni_zadatak['uzmi_lokacija'])
        else: # ST_KRETANJE_DO_ODLAGALISTA
            cilj = tuple(self.agent.trenutni_zadatak['odnesi_lokacija'])

        start = self.agent.pozicija
        putanja = astar(SKLADISTE_MAPA, start, cilj)

        if not putanja:
            print(f"[{self.agent.jid}] Nema putanje od {start} do {cilj}. Čekam...")
            self.agent.ciljni_state_nakon_cekanja = current_state_name
            self.set_next_state(ST_CEKANJE_NA_PUT)
            return

        msg_body = json.dumps({"PATH_RESERVATION_REQUEST": True, "putanja": putanja})
        msg = spade.message.Message(to=self.agent.dispecer_jid, body=msg_body)
        msg.set_metadata("performative", "request")
        await self.send(msg)

        reply = await self.receive(timeout=10)
        if reply and reply.metadata.get("performative") == "confirm":
            poruka = f"Robot {self.agent.jid.localpart}: Putanja odobrena, krećem se od {start} do {cilj}."
            self.agent.shared_state.azuriraj_status_poruku(poruka)
            for korak_pozicija in putanja[1:]:
                self.agent.pozicija = korak_pozicija
                self.agent.shared_state.azuriraj_poziciju_robota(str(self.agent.jid), self.agent.pozicija)
                await asyncio.sleep(0.3)
            
            if current_state_name == ST_KRETANJE_PO_PAKET:
                self.set_next_state(ST_KRETANJE_DO_ODLAGALISTA)
            else:
                poruka = f"Robot {self.agent.jid.localpart}: Zadatak završen."
                self.agent.shared_state.azuriraj_status_poruku(poruka)
                self.set_next_state(ST_CEKANJE_ZADATKA)
        else:
            poruka = f"Robot {self.agent.jid.localpart}: Putanja odbijena, čekam."
            self.agent.shared_state.azuriraj_status_poruku(poruka)
            self.agent.ciljni_state_nakon_cekanja = current_state_name
            self.set_next_state(ST_CEKANJE_NA_PUT)

class StanjeCekanjaNaPut(spade.behaviour.State):
    """Stanje u koje robot ulazi kada je putanja odbijena. Čeka kratko vrijeme prije novog pokušaja."""
    async def run(self):
        poruka = f"Robot {self.agent.jid.localpart}: Putanja zauzeta, čekam prije novog pokušaja."
        self.agent.shared_state.azuriraj_status_poruku(poruka)
        await asyncio.sleep(2)
        self.set_next_state(self.agent.ciljni_state_nakon_cekanja)

# --- GLAVNA KLASA AGENTA ROBOTA ---

class AgentRobot(spade.agent.Agent):
    """
    Agent Robot predstavlja autonomnog robota u skladištu koji izvršava
    zadatke prijevoza robe. Njegovo ponašanje je upravljano konačnim automatom (FSM).
    Komunicira s Dispečerom radi dobivanja zadataka i rezervacije putanja.
    """
    def __init__(self, jid, password, dispecer_jid, pocetna_pozicija, shared_state, verify_security=False):
        super().__init__(jid, password, verify_security)
        self.dispecer_jid = dispecer_jid
        self.pozicija = pocetna_pozicija
        self.trenutni_zadatak = None
        self.ciljni_state_nakon_cekanja = None
        self.shared_state = shared_state

    async def setup(self):
        print(f"Agent Robot {self.jid} se pokrenuo na poziciji {self.pozicija}.")
        self.shared_state.azuriraj_poziciju_robota(str(self.jid), self.pozicija)

        fsm = FSMBehaviour()
        fsm.add_state(name=ST_CEKANJE_ZADATKA, state=StanjeCekanjaZadatka(), initial=True)
        fsm.add_state(name=ST_KRETANJE_PO_PAKET, state=StanjeKretanja())
        fsm.add_state(name=ST_KRETANJE_DO_ODLAGALISTA, state=StanjeKretanja())
        fsm.add_state(name=ST_CEKANJE_NA_PUT, state=StanjeCekanjaNaPut())

        # Tranzicije
        fsm.add_transition(source=ST_CEKANJE_ZADATKA, dest=ST_KRETANJE_PO_PAKET)
        fsm.add_transition(source=ST_CEKANJE_ZADATKA, dest=ST_CEKANJE_ZADATKA) # Ako nema zadatka
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_KRETANJE_DO_ODLAGALISTA)
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_ZADATKA)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_PO_PAKET)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_DO_ODLAGALISTA)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_CEKANJE_ZADATKA) # Fallback

        self.add_behaviour(fsm)