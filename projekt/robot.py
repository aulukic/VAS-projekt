import spade
import json
import asyncio
from pathfinding import astar
from skladiste import SKLADISTE_MAPA

ST_CEKANJE_ZADATKA = "ST_CEKANJE_ZADATKA"
ST_KRETANJE_PO_PAKET = "ST_KRETANJE_PO_PAKET"
ST_KRETANJE_DO_ODLAGALISTA = "ST_KRETANJE_DO_ODLAGALISTA"
ST_CEKANJE_NA_PUT = "ST_CEKANJE_NA_PUT"

class FSMBehaviour(spade.behaviour.FSMBehaviour):
    async def on_start(self):
        print(f"FSM za {self.agent.jid} pokrenut. Početno stanje: {self.behaviour.current_state}")
    async def on_end(self):
        print(f"FSM za {self.agent.jid} završen.")
        await self.agent.stop()

class StanjeCekanjaZadatka(spade.behaviour.State):
    async def run(self):
        print(f"[{self.agent.jid}] Tražim novi zadatak od dispečera...")
        msg = spade.message.Message(to=self.agent.dispecer_jid, body=json.dumps({"tip": "REQUEST_TASK"}))
        msg.set_metadata("performative", "request")
        await self.send(msg)
        reply = await self.receive(timeout=10)
        if reply and reply.metadata.get("performative") == "inform":
            task_data = json.loads(reply.body)
            if task_data.get("status") == "NEMA_ZADATAKA":
                 print(f"[{self.agent.jid}] Nema zadatka, čekam...")
                 await asyncio.sleep(5)
                 self.set_next_state(ST_CEKANJE_ZADATKA)
            else:
                self.agent.trenutni_zadatak = task_data
                print(f"[{self.agent.jid}] Dobio zadatak: {self.agent.trenutni_zadatak}")
                self.set_next_state(ST_KRETANJE_PO_PAKET)
        else:
            print(f"[{self.agent.jid}] Nema odgovora od dispečera, pokušavam ponovo...")
            await asyncio.sleep(2)
            self.set_next_state(ST_CEKANJE_ZADATKA)

class StanjeKretanja(spade.behaviour.State):
    async def run(self):
        # OVO JE KLJUČNI ISPRAVAK:
        # Pristupamo imenu stanja preko automata (`self.behaviour`), a ne preko samog stanja (`self`)
        is_moving_to_package = self.behaviour.current_state == ST_KRETANJE_PO_PAKET
        
        if is_moving_to_package:
            cilj = tuple(self.agent.trenutni_zadatak['uzmi_lokacija'])
        else:
            cilj = tuple(self.agent.trenutni_zadatak['odnesi_lokacija'])

        start = self.agent.pozicija
        putanja = astar(SKLADISTE_MAPA, start, cilj)

        if not putanja:
            self.agent.ciljni_state_nakon_cekanja = self.behaviour.current_state
            self.set_next_state(ST_CEKANJE_NA_PUT)
            return

        putanja_s_vremenom = [(p[0], p[1], t) for t, p in enumerate(putanja, start=1)]
        msg = spade.message.Message(to=self.agent.dispecer_jid, body=json.dumps({"tip": "PATH_RESERVATION_REQUEST", "putanja": putanja_s_vremenom}))
        msg.set_metadata("performative", "request")
        await self.send(msg)
        reply = await self.receive(timeout=10)

        if reply and reply.metadata.get("performative") == "confirm":
            for korak_pozicija in putanja[1:]:
                self.agent.pozicija = korak_pozicija
                self.agent.shared_state.azuriraj_poziciju_robota(str(self.agent.jid), self.agent.pozicija)
                await asyncio.sleep(0.3)
            
            if is_moving_to_package:
                self.set_next_state(ST_KRETANJE_DO_ODLAGALISTA)
            else:
                print(f"[{self.agent.jid}] Zadatak završen, šaljem zahtjev za brisanje rezervacija.")
                clear_msg = spade.message.Message(to=self.agent.dispecer_jid, body=json.dumps({"tip": "CLEAR_RESERVATIONS"}))
                clear_msg.set_metadata("performative", "request")
                await self.send(clear_msg)
                
                self.set_next_state(ST_CEKANJE_ZADATKA)
        else:
            self.agent.ciljni_state_nakon_cekanja = self.behaviour.current_state
            self.set_next_state(ST_CEKANJE_NA_PUT)

class StanjeCekanjaNaPut(spade.behaviour.State):
    async def run(self):
        print(f"[{self.agent.jid}] Putanja zauzeta, čekam...")
        await asyncio.sleep(2)
        if self.agent.ciljni_state_nakon_cekanja:
             self.set_next_state(self.agent.ciljni_state_nakon_cekanja)
        else:
             self.set_next_state(ST_CEKANJE_ZADATKA)

class AgentRobot(spade.agent.Agent):
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
        fsm.add_transition(source=ST_CEKANJE_ZADATKA, dest=ST_CEKANJE_ZADATKA)
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_KRETANJE_DO_ODLAGALISTA)
        fsm.add_transition(source=ST_KRETANJE_PO_PAKET, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_ZADATKA)
        fsm.add_transition(source=ST_KRETANJE_DO_ODLAGALISTA, dest=ST_CEKANJE_NA_PUT)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_PO_PAKET)
        fsm.add_transition(source=ST_CEKANJE_NA_PUT, dest=ST_KRETANJE_DO_ODLAGALISTA)
        self.add_behaviour(fsm)