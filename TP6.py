import webbrowser
from pathlib import Path
from ivy.ivy import IvyServer
from bs4 import BeautifulSoup

class Concurrent(IvyServer):
    def __init__(self, name):

        IvyServer.__init__(self, "IvyServer")
        self.name = name
        self.start('127.255.255.255:2010')
        self.bind_msg(self.handle_msg, "^ppilot5 Answer=Finished$")
        print("here")
        self.texte="""<h1>Toulouse, Ville Rose</h1>

        <h2>Histoire  et géographie</h2>
        <b>Toulouse</b> (en occitan, <i>Tolosa</i> /tuˈluzɔ/) est une commune du Sud-Ouest de la France. 
        <p>Capitale au Vème siècle du royaume wisigoth, capitale du <u>comté de Toulouse</u> fondé en 852 par Raimond Ier et capitale historique du Languedoc, elle est aujourd'hui le chef-lieu de la région Occitanie et du département de la Haute-Garonne.
        
        <h2>Lieux remarquables</h2>
        <ul>
            <li>Reliant Toulouse à Sète, le <u>canal du Midi</u> est inscrit au patrimoine mondial de l'Unesco depuis 1996.</li>
            <li>La <u>basilique Saint-Sernin</u>, plus grand édifice roman d'Europe, y est également inscrite depuis 1998 au titre des chemins de Saint-Jacques de Compostelle.</li>
        </ul>
        
        <h2>Sport</h2>
        Le sport emblématique de Toulouse est le <b>rugby à XV</b>, son club du <b>Stade Toulousain</b> détenant le plus riche palmarès sur le plan national comme sur le plan continental, avec vingt-et-un titres de champion de France et cinq titres de champion d'Europe.
        
        <h2>Gastronomie</h2>
        Le <b>cassoulet</b>, la <b>saucisse</b> et la <b>violette</b> sont les spécialités emblématiques de la gastronomie toulousaine."""

        path = Path("temp.html").resolve()
        path.write_text(self.texte, encoding="utf-8")

        webbrowser.open(path.as_uri())

        soup = BeautifulSoup(self.texte, "html.parser")
        self.tags = [tag.name for tag in soup.find_all()]
        self.wait=False


    def handle_msg(self, agent, numid, garbage):
        self.wait=False

    def run(self):
        for tag in self.tags:
            while not self.wait:
                print(tag)
                self.send_msg(f"ppilot5 Say= {tag}")
                self.send_msg("Braille_display Text=" + tag)
                self.wait=True


a=Concurrent("Concurrent")
a.run()