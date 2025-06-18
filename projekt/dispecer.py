import spade
import json
from collections import deque
from skladiste import ZADACI

class AgentDispecer(spade.agent.Agent):
    """
    Agent Dispečer je centralna jedinica sustava. Upravlja listom zadataka,
    dodjeljuje ih slobodnim robotima i koordinira kretanje odobravanjem ili
    odbijanjem zahtjeva za rezervaciju putanje kako bi se spriječili sudari.
    """
    def __init__(self, jid, password, shared_state, verify_security=False):
        super().__init__(jid, password, verify_security)
        self.lista_zadataka = deque(ZADACI)
        self.status_robota = {}
        self.tablica_rezervacija = {}
        self.shared_state = shared_state

    class PonasanjeDodjeleZadataka(spade.behaviour.CyclicBehaviour):
        """Ovo ponašanje kontinuirano sluša zahtjeve robota za novim zadacima."""
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and msg.metadata.get("performative") == "request" and msg.body == "REQUEST_TASK":
                robot_jid_str = str(msg.sender)
                if self.agent.lista_zadataka:
                    zadatak = self.agent.lista_zadataka.popleft()
                    self.agent.status_robota[robot_jid_str] = 'zauzet'
                    
                    reply = spade.message.Message(to=robot_jid_str)
                    reply.set_metadata("performative", "inform")
                    reply.body = json.dumps(zadatak)
                    await self.send(reply)

                    poruka = f"Dispečer: Dodijelio zadatak robotu {msg.sender.localpart}."
                    self.agent.shared_state.azuriraj_status_poruku(poruka)
                else:
                    reply = spade.message.Message(to=robot_jid_str)
                    reply.set_metadata("performative", "inform")
                    reply.body = json.dumps({"status": "NEMA_ZADATAKA"})
                    await self.send(reply)

    class PonasanjeRezervacijePutanja(spade.behaviour.CyclicBehaviour):
        """Ovo ponašanje kontinuirano obrađuje zahtjeve za rezervaciju putanja."""
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg and msg.metadata.get("performative") == "request" and "PATH_RESERVATION_REQUEST" in msg.body:
                robot_jid_str = str(msg.sender)
                try:
                    data = json.loads(msg.body)
                    putanja_za_rezervaciju = [tuple(p) for p in data["putanja"]]
                    
                    ima_konflikta = False
                    for korak in putanja_za_rezervaciju:
                        if korak in self.agent.tablica_rezervacija and self.agent.tablica_rezervacija[korak] != robot_jid_str:
                            ima_konflikta = True
                            poruka = f"Dispečer: ODBIO putanju za {msg.sender.localpart} zbog konflikta."
                            self.agent.shared_state.azuriraj_status_poruku(poruka)
                            break
                    
                    reply = spade.message.Message(to=robot_jid_str)
                    if not ima_konflikta:
                        for korak in putanja_za_rezervaciju:
                            self.agent.tablica_rezervacija[korak] = robot_jid_str
                        reply.set_metadata("performative", "confirm")
                        reply.body = "PATH_RESERVATION_CONFIRM"
                        poruka = f"Dispečer: ODOBRIO putanju za {msg.sender.localpart}."
                        self.agent.shared_state.azuriraj_status_poruku(poruka)
                    else:
                        reply.set_metadata("performative", "failure")
                        reply.body = "PATH_RESERVATION_DENY"
                        
                    await self.send(reply)
                except (json.JSONDecodeError, KeyError):
                    pass

    async def setup(self):
        print(f"Agent Dispečer {self.jid} se pokrenuo.")
        self.add_behaviour(self.PonasanjeDodjeleZadataka())
        self.add_behaviour(self.PonasanjeRezervacijePutanja())