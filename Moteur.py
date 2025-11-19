from ivy.ivy import IvyServer
class Moteur(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, name)
        print("start")
        self.start('127.0.0.1:2010')
        self.bind_msg(self.handle_msg, "sra5 Parsed=action=(.*) where=(.*) form=(.*) color=(.*) localisation=(.*) Confidence=(.*) NP=.*")
        self.bind_msg(self.handle_palette_msg, r"Palette Click x=(.*) y=(.*)")
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

    def handle_msg_vocal(self, agent, action, where, form, color, localisation, confidence):
        print("handle vocal")
        if float(confidence.replace(",", ".")) > 0.50:
            self.action = action
            self.where = where
            if self.forme=='':
                self.forme = form
            self.couleur = color
            self.localisation = localisation
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")

    def handle_msg_geste(self, agent, form, confidence):
        print(confidence)
        if float(confidence) > 0.50:
            self.forme = form
            print(form)
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")
    def handle_palette_msg(self, agent, event):
        try:
            x = int(event[0])
            y = int(event[1])
            self.coordonnee.append([x, y])

            print(f"[Palette] Coordonnée ajoutée : ({x}, {y})")
            print(f"[Palette] Liste actuelle : {self.coordonnee}")

        except Exception as e:
            print("[Palette] Erreur parsing coordonnées :", e)



Moteur=Moteur("Moteur")

