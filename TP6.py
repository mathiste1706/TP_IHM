import webbrowser
from pathlib import Path
from ivy.ivy import IvyServer
from bs4 import BeautifulSoup
import time

class TP6Engine(IvyServer):

    def __init__(self, name):

        IvyServer.__init__(self, name)
        self.name = name
        self.start("127.255.255.255:2010")

        # Notification de fin de lecture TTS
        self.bind_msg(self.handle_tts_finished, "^ppilot5 Answer=Finished$")

        # ----- MODE : concurrent / synergic -----
        self.mode = "concurrent"

        # ----- Charger / parser le HTML -----
        self.texte = """
        <h1>Toulouse, Ville Rose</h1>

        <h2>Histoire  et géographie</h2>
        <b>Toulouse</b> (en occitan, <i>Tolosa</i>) est une commune du Sud-Ouest de la France.
        <p>Capitale au Vème siècle du royaume wisigoth (...)</p>

        <h2>Lieux remarquables</h2>
        <p>Reliant Toulouse à Sète, le <u>canal du Midi</u> est inscrit au patrimoine mondial.</p>

        <h2>Sport</h2>
        <p>Le sport emblématique est le <b>rugby à XV</b> (...)</p>

        <h2>Gastronomie</h2>
        <p>Le <b>cassoulet</b>, la <b>saucisse</b> et la <b>violette</b> sont typiques.</p>
        """

        path = Path("toulouse.html")
        path.write_text(self.texte, encoding="utf-8")
        #webbrowser.open(path.as_uri())

        self.segments = self.parse_segments(self.texte)
        self.index = 0
        self.wait = False 

    # ----------------------------------------------------------------
    #           PARSER HTML -> SEGMENTS
    # ----------------------------------------------------------------
    def parse_segments(self, html):
        soup = BeautifulSoup(html, "html.parser")
        segments = []

        for tag in soup.find_all(["h1", "h2", "p", "b"]):

            text = tag.get_text(strip=True)
            if not text:
                continue

            seg = {
                "texte": text,
                "type": tag.name,
                "gras": tag.name == "b" or tag.find("b") is not None,
                "italique": tag.find("i") is not None,
                "taille": "grand" if tag.name == "h1" else ("moyen" if tag.name == "h2" else "normal")
            }
            segments.append(seg)

        return segments

    #           GESTION FIN DE LECTURE DE PPILOT5
    def handle_tts_finished(self, agent, numid, garbage):
        self.wait = False

    #           ENVOIS MULTIMODAUX

    def send_braille(self, message):
        message = message[:10]
        self.send_msg(f"Braille_display Text={message}")

    def send_tts_text(self, message):
        self.send_msg(f"ppilot5 Say={message}")

    def send_tts_ssml(self, ssml):
        self.send_msg(f"ppilot5 SSML={ssml}")

    #           FISSION MODES

    def fission_concurrent(self, seg):
        prefix = ""
        if seg["type"] == "h1": prefix += "[H1]"
        if seg["type"] == "h2": prefix += "[H2]"
        if seg["gras"]: prefix += "[G]"
        if seg["italique"]: prefix += "[I]"

        self.send_braille(prefix)
        self.send_tts_text(seg["texte"])

    def fission_synergic(self, seg):

        attrs = []
        if seg["type"] == "h1": attrs.append("H1")
        if seg["type"] == "h2": attrs.append("H2")
        if seg["gras"]: attrs.append("G")
        if seg["italique"]: attrs.append("I")
        braille = " ".join(attrs)[:10] or "TXT"

        self.send_braille(braille)
        self.send_tts_text(seg["texte"])

    #           LOOP
    def run(self):
        while self.index < len(self.segments):
            seg = self.segments[self.index]

            # choisir le mode
            if self.mode == "concurrent":
                self.fission_concurrent(seg)
            elif self.mode == "synergic":
                self.fission_synergic(seg)

            self.wait = True
            while self.wait:
                time.sleep(0.1)

            self.index += 1


if __name__ == "__main__":
    moteur = TP6Engine("TP6")
    moteur.run()
