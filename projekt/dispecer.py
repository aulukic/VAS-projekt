import spade
import json
from collections import deque
from skladiste import ZADACI

class AgentDispecer(spade.agent.Agent):
    """
    Agent Dispečer je centralna jedinica sustava. Koristi jedno glavno ponašanje
    koje usmjerava poruke kako bi se izbjegli interni konflikti.
    """
    def __init__(self, jid, password, shared_state, verify_security=False):
        super().__init__(jid, password, verify_security)
        self.lista_zadataka = deque(ZADACI)
        self.tablica_rezervacija = {}
        self.shared_state = shared_state

    # Sva logika je sada unutar jednog ponašanja
    class PonasanjeDispecera(spade.behaviour.CyclicBehaviour):
        async def run(self):
            # Čekaj na bilo koju poruku
            msg = await self.receive(timeout=10)
            if msg and msg.metadata.get("performative") == "request":
                try:
                    data = json.loads(msg.body)
                    tip_poruke = data.get("tip")
                    
                    # --- ROUTER LOGIKA ---
                    if tip_poruke == "REQUEST_TASK":
                        await self.obradi_zahtjev_za_zadatkom(msg)
                    elif tip_poruke == "PATH_RESERVATION_REQUEST":
                        await self.obradi_rezervaciju_putanje(msg, data)
                    elif tip_poruke == "CLEAR_RESERVATIONS":
                        await self.obradi_brisanje_rezervacija(msg)

                except (json.JSONDecodeError, KeyError):
                    # Ignoriraj neispravne poruke
                    print(f"Dispečer: Primio neispravnu poruku od {msg.sender.localpart}")
                    pass

        async def obradi_zahtjev_za_zadatkom(self, msg):
            robot_jid_str = str(msg.sender)
            if self.agent.lista_zadataka:
                zadatak = self.agent.lista_zadataka.popleft()
                reply = spade.message.Message(to=robot_jid_str, body=json.dumps(zadatak))
                reply.set_metadata("performative", "inform")
                await self.send(reply)
                poruka = f"Dispečer: Dodijelio zadatak robotu {msg.sender.localpart}."
                self.agent.shared_state.azuriraj_status_poruku(poruka)
            else:
                reply = spade.message.Message(to=robot_jid_str, body=json.dumps({"status": "NEMA_ZADATAKA"}))
                reply.set_metadata("performative", "inform")
                await self.send(reply)

        async def obradi_rezervaciju_putanje(self, msg, data):
            robot_jid_str = str(msg.sender)
            putanja = [tuple(p) for p in data["putanja"]]
            ima_konflikta = any(korak in self.agent.tablica_rezervacija and self.agent.tablica_rezervacija[korak] != robot_jid_str for korak in putanja)
            
            reply = spade.message.Message(to=robot_jid_str)
            if not ima_konflikta:
                for korak in putanja:
                    self.agent.tablica_rezervacija[korak] = robot_jid_str
                reply.set_metadata("performative", "confirm")
                poruka = f"Dispečer: ODOBRIO putanju za {msg.sender.localpart}."
                self.agent.shared_state.azuriraj_status_poruku(poruka)
            else:
                reply.set_metadata("performative", "failure")
                poruka = f"Dispečer: ODBIO putanju za {msg.sender.localpart} zbog konflikta."
                self.agent.shared_state.azuriraj_status_poruku(poruka)
            await self.send(reply)

        async def obradi_brisanje_rezervacija(self, msg):
            robot_jid_str = str(msg.sender)
            kljucevi_za_brisanje = [k for k, v in self.agent.tablica_rezervacija.items() if v == robot_jid_str]
            for kljuc in kljucevi_za_brisanje:
                del self.agent.tablica_rezervacija[kljuc]
            poruka = f"Dispečer: Obrisao rezervacije za robota {msg.sender.localpart}."
            self.agent.shared_state.azuriraj_status_poruku(poruka)
            # Nije potrebno slati odgovor na brisanje rezervacija

    async def setup(self):
        print(f"Agent Dispečer {self.jid} se pokrenuo.")
        # Dodaje se samo jedno, glavno ponašanje
        self.add_behaviour(self.PonasanjeDispecera())