import spade
import asyncio
import json
from pathfinding import astar
from skladiste import SKLADISTE_MAPA

ST_CEKANJE_ZADATKA = "ST_CEKANJE_ZADATKA"
ST_KRETANJE_PO_PAKET = "ST_KRETANJE_PO_PAKET"
ST_KRETANJE_DO_ODLAGALISTA = "ST_KRETANJE_DO_ODLAGALISTA"
ST_CEKANJE_NA_PUT = "ST_CEKANJE_NA_PUT"

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

        fsm.add_transition(source=ST_CEKANJE_ZADATKA, dest=ST_KRETANJE_PO_PAKET)
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_KRETANJE_DO_ODLAGALISTA)
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_ZADATKA)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_PO_PAKET)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_DO_ODLAGALISTA)

        self.add_behaviour(fsm)

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
        msg = spade.message.Message(to=self.agent.dispecer_jid, body="REQUEST_TASK")
        msg.set_metadata("performative", "request")
        await self.send(msg)

        reply = await self.receive(timeout=10)
        if reply and reply.body:
            data = json.loads(reply.body)
            if "uzmi_lokacija" in data:
                self.agent.trenutni_zadatak = data
                self.set_next_state(ST_KRETANJE_PO_PAKET)
            else:
                print(f"[{self.agent.jid}] Nema više zadataka. Gasim se.")
        else:
            print(f"[{self.agent.jid}] Nisam dobio odgovor od dispečera. Pokušavam ponovo.")

class StanjeKretanja(spade.behaviour.State):
    """
    Stanje koje obuhvaća izračun putanje, zahtjev za rezervaciju i simulaciju
    kretanja do cilja (bilo po paket ili na odlagalište).
    """
    async def run(self):
        if self.current_state == ST_KRETANJE_PO_PAKET:
            start = self.agent.pozicija
            cilj = tuple(self.agent.trenutni_zadatak['uzmi_lokacija'])
        else:
            start = self.agent.pozicija
            cilj = tuple(self.agent.trenutni_zadatak['odnesi_lokacija'])

        putanja = astar(SKLADISTE_MAPA, start, cilj)
        if not putanja:
            self.agent.ciljni_state_nakon_cekanja = self.current_state
            self.set_next_state(ST_CEKANJE_NA_PUT)
            return

        putanja_s_vremenom = [(p[0], p[1], t) for t, p in enumerate(putanja, start=1)]
        msg_body = json.dumps({"tip": "PATH_RESERVATION_REQUEST", "putanja": putanja_s_vremenom})
        msg = spade.message.Message(to=self.agent.dispecer_jid, body=msg_body)
        msg.set_metadata("performative", "request")
        await self.send(msg)

        reply = await self.receive(timeout=10)
        if reply:
            if reply.metadata.get("performative") == "confirm":
                for korak_pozicija in putanja[1:]:
                    self.agent.pozicija = korak_pozicija
                    self.agent.shared_state.azuriraj_poziciju_robota(str(self.agent.jid), self.agent.pozicija)
                    await asyncio.sleep(0.3)

                if self.current_state == ST_KRETANJE_PO_PAKET:
                    self.set_next_state(ST_KRETANJE_DO_ODLAGALISTA)
                else:
                    self.agent.shared_state.azuriraj_status_poruku(f"Robot {self.agent.jid.localpart} je završio zadatak i slobodan je.")
                    self.set_next_state(ST_CEKANJE_ZADATKA)
            else:
                self.agent.ciljni_state_nakon_cekanja = self.current_state
                self.set_next_state(ST_CEKANJE_NA_PUT)
        else:
            self.agent.ciljni_state_nakon_cekanja = self.current_state
            self.set_next_state(ST_CEKANJE_NA_PUT)

class StanjeCekanjaNaPut(spade.behaviour.State):
    """Stanje u koje robot ulazi kada je putanja odbijena. Čeka kratko vrijeme prije novog pokušaja."""
    async def run(self):
        vrijeme_cekanja = 2
        poruka_cekanja = f"Robot {self.agent.jid.localpart} čeka jer je put zauzet."
        self.agent.shared_state.azuriraj_status_poruku(poruka_cekanja)
        await asyncio.sleep(vrijeme_cekanja)
        self.set_next_state(self.agent.ciljni_state_nakon_cekanja)