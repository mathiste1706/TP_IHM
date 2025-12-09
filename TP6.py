import webbrowser
from pathlib import Path
from ivy.ivy import IvyServer
from bs4 import BeautifulSoup, NavigableString, Tag
import time
import threading

SUPPORTED = {"h1", "h2", "b", "i", "u"}
IGNORED = {"p"}

class TP6Engine(IvyServer):

    def __init__(self, name):
        IvyServer.__init__(self, name)
        self.start("127.255.255.255:2010")

        self.bind_msg(self.handle_tts_finished, "^ppilot5 Answer=Finished$")

        self.mode = "concurrent"
        self.playing = True
        self.wait = False
        self.index = 0
        self.just_reset = False

        self.html = """
        <h1>Toulouse, Ville Rose</h1>

        <h2>Histoire et géographie</h2>
        <b>Toulouse</b> (en occitan, <i>Tolosa</i>) est une commune du Sud-Ouest de la France.
        <p>Capitale au Vème siècle du royaume wisigoth (...)</p>

        <h2>Lieux remarquables</h2>
        <p>Reliant Toulouse à Sète, le <u>canal du Midi</u> est inscrit au patrimoine mondial.</p>

        <h2>Sport</h2>
        <p>Le sport emblématique est le <b>rugby à XV</b> (...)</p>

        <h2>Gastronomie</h2>
        <p>Le <b>cassoulet</b>, la <b>saucisse</b> et la <b>violette</b> sont typiques.</p>
        """

        path = Path("toulouse.html").resolve()
        path.write_text(self.html, encoding="utf-8")
        webbrowser.open(path.as_uri())

        self.events = self.parse_html_events(self.html)
        self.tag = None

    # ---------- PARSE HTML ----------
    def parse_html_events(self, html):
        soup = BeautifulSoup(html, "html.parser")
        events = []

        def walk(node):
            if isinstance(node, NavigableString):
                text = node.strip()
                if text:
                    events.append(("text", text))
                return

            if isinstance(node, Tag):
                tag = node.name.lower()

                # Ignorer complètement <p>
                if tag in IGNORED:
                    for c in node.children:
                        walk(c)
                    return

                if tag in SUPPORTED:
                    events.append(("open", tag))

                for c in node.children:
                    walk(c)

                if tag in SUPPORTED:
                    events.append(("close", tag))

        for c in soup.children:
            walk(c)

        return events

    # ---------- CALLBACK FIN TTS ----------
    def handle_tts_finished(self, agent, *args):
        self.wait = False

    # ---------- ENVOIS ----------
    def send_braille(self, msg):
        self.send_msg(f"Braille_display Text={msg[:10]}")

    def send_tts(self, msg):
        self.send_msg(f"ppilot5 Say={msg}")

    # ---------- UPDATE BRAILLE ----------
    def update_braille(self):
        if self.tag is None:
            self.send_braille("")
        else:
            self.send_braille(self.tag.upper())

    # ---------- CONCURRENT MODE ----------
    def process_event_concurrent(self, event):
        etype, val = event

        if etype == "open":
            self.tag = val
            self.update_braille()
            self.wait = True
            self.send_tts(f"balise {val.upper()} ouvrante")

        elif etype == "text":
            self.wait = True
            self.send_tts(val)

        elif etype == "close":
            self.wait = True
            self.send_tts(f"balise {val.upper()} fermante")
            self.tag = None
            self.update_braille()

    # ---------- SYNERGIC MODE ----------
    def process_event_synergic(self, event):
        etype, val = event

        if etype == "open":
            self.tag = val
            self.update_braille()
            time.sleep(0.05)

        elif etype == "close":
            self.tag = None
            self.update_braille()
            time.sleep(0.05)

        elif etype == "text":
            self.wait = True
            self.send_tts(val)
            while self.wait:
                time.sleep(0.05)

    # ---------- CONTROLES ----------
    def play(self):
        self.playing = True

    def pause(self):
        self.playing = False

    def reset(self):
        self.index = 0
        self.tag = None
        self.just_reset = True  # active le flag

    # ---------- LOOP ----------
    def run(self):
        while self.index < len(self.events):

            if not self.playing:
                time.sleep(0.1)
                continue

            event = self.events[self.index]

            if self.mode == "concurrent":
                self.process_event_concurrent(event)
                while self.wait:
                    time.sleep(0.05)

            else:
                self.process_event_synergic(event)
                time.sleep(0.05)

            self.index += 1

            # Si reset juste fait, revenir sur le premier événement
            if self.just_reset:
                self.index = 0
                self.just_reset = False

# ---------- MAIN ----------
if __name__ == "__main__":
    moteur = TP6Engine("TP6")

    # lancer la lecture dans un thread pour pouvoir contrôler depuis la console
    t = threading.Thread(target=moteur.run)
    t.start()

    # boucle console simple pour tester play/pause/reset
    while True:
        cmd = input("cmd (p=Pause, r=Reset) > ").strip().lower()
        if cmd == "p" and moteur.playing:
            moteur.pause()
            print("Lecture en pause")
        elif cmd == "p" and not moteur.playing:
            moteur.play()
            print("Reprise de la lecture")
        elif cmd == "r":
            moteur.reset()
            print("Retour au début")
