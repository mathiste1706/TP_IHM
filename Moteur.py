from ivy.ivy import IvyServer
class Moteur(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, name)
        self.start('127.0.0.1:2010')
        self.bind_msg(self.handle_msg, "sra5 Parsed=action=(.*) where=(.*) form=(.*) color=(.*) localisation=(.*) Confidence=(.*) NP=.*")
        self.bind_msg(self.handle_palette_click, r"Palette Click x=(.*) y=(.*)")


        self.name = name
        self.action = ""
        self.forme = ""
        self.couleur = ""
        self.localisation = []
        self.coordonnee = []

    def fuisionnable(self):
        if self.action != "" and self.forme != "" and self.localisation != []:
            return True
        return False

    def handle_msg(self, agent, numid, action, where, form, color, localisation, confidence):
        if float(confidence.replace(",", ".")) > 0.50:
            self.action = action
            self.where = where
            self.forme = form
            self.couleur = color
            self.localisation = localisation
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")
    
    def handle_palette_click(self, agent, event):
        try:
            x = int(event[0])
            y = int(event[1])
            self.coordonnee.append([x, y])
            print(f"[Palette] Clic reçu : x={x}, y={y}")

        except Exception as e:
            print("[Palette] Erreur parsing coordonnées :", e)



Moteur=Moteur("Moteur")

