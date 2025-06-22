Višeagentni sustav za koordinaciju robota u skladištu (VAS-projekt)
Ovaj projekt je simulacija automatiziranog skladišta implementirana u Pythonu korištenjem višeagentnog sustava. Agenti (roboti) autonomno preuzimaju zadatke prijevoza robe, izračunavaju optimalne putanje pomoću A* algoritma i međusobno komuniciraju s centralnim agentom (Dispečerom) kako bi rezervirali svoje rute i izbjegli sudare. Stanje sustava i kretanje robota vizualizirano je u stvarnom vremenu unutar terminala.

Popis Alata
Za pokretanje ovog projekta potrebno je imati instalirane sljedeće alate:

Python (verzija 3.9)

Miniconda ili Anaconda (za upravljanje virtualnim okruženjima)

Instalacija i Postavljanje
Pratite ove korake kako biste postavili i pokrenuli projekt na svom računalu.

1. Klonirajte Repozitorij

Otvorite terminal ili Git Bash i klonirajte ovaj repozitorij na svoje lokalno računalo:

git clone [https://github.com/aulukic/VAS-projekt.git](https://github.com/aulukic/VAS-projekt.git)
cd VAS-projekt

2. Kreirajte i Aktivirajte Conda Okruženje

Preporučuje se korištenje virtualnog okruženja kako bi se izbjegli konflikti s drugim Python projektima.

# Kreirajte novo okruženje naziva "vas-projekt" s Pythonom 3.9
conda create --name vas-projekt python=3.9 -y

# Aktivirajte novokreirano okruženje
conda activate vas-projekt

3. Instalirajte Potrebne Biblioteke

Projekt koristi biblioteke navedene u zahtjevi.txt datoteci. Instalirajte ih sljedećom naredbom:

pip install -r zahtjevi.txt

Pokretanje Simulacije
Nakon što ste uspješno završili instalaciju, simulaciju možete pokrenuti jednom jednostavnom naredbom iz glavnog direktorija projekta:

python main.py

Sustav će se pokrenuti, a u terminalu ćete vidjeti animirani prikaz skladišta i kretanja robota. Za prekid simulacije, pritisnite CTRL+C u terminalu.

Važna napomena: XMPP Poslužitelj
Ovaj projekt koristi spade radni okvir koji za komunikaciju između agenata zahtijeva XMPP poslužitelj.

Automatsko pokretanje: Prilikom pokretanja skripte main.py, spade će automatski pokušati pokrenuti vlastiti ugrađeni XMPP poslužitelj na localhost adresi (port 5222). U većini slučajeva, nisu potrebne nikakve dodatne radnje.

Ručna registracija agenata: Nije potrebna. Kod koristi opciju auto_register=True, što znači da će se agenti (npr. dispecer@localhost, robot1@localhost) sami registrirati na poslužitelju pri prvom pokretanju.

Mogući problemi: Ako se aplikacija ne pokrene ili prijavi grešku vezanu za mrežu, mogući uzrok je da je port 5222 zauzet od strane druge aplikacije na vašem računalu.

Struktura Projekta
main.py: Glavna skripta koja inicijalizira sve agente, pokreće simulaciju i upravlja vizualizacijom u terminalu.

robot.py: Sadrži logiku za AgentaRobota, uključujući njegov konačni automat (FSM) za upravljanje stanjima (čekanje, kretanje, itd.).

dispecer.py: Sadrži logiku za AgentaDispečera koji dodjeljuje zadatke i rješava konflikte rezervacijom putanja.

skladiste.py: Definira 2D mapu skladišta, početne pozicije i listu zadataka za transport.

pathfinding.py: Sadrži implementaciju A* (A-zvijezda) algoritma za pronalaženje najkraćeg puta.

zahtjevi.txt: Popis Python biblioteka potrebnih za projekt.
