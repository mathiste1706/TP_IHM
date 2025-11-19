from ivy.ivy import IvyServer
class Moteur(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, name)
        print("start")
        self.start('127.255.255.255:2010')
        self.bind_msg(self.handle_msg_vocal, "sra5 Parsed=action=(.*) where=(.*) form=(.*) color=(.*) localisation=(.*) Confidence=(.*) NP=.* Num_A=.*")
        self.bind_msg(self.handle_msg_geste,"NDOLLAR_RECO name=(.*) score=(.*)")
        self.bind_msg(self.handle_msg_palette, r"Palette Click x=(.*) y=(.*)")

        self.bind_msg(
            lambda agent, *groups: print("[BUS MESSAGE]", repr(groups), "AGENT:", agent),
            "(.*)"
        )

        self.name = name
        self.where=""
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

    def handle_msg_palette(self, agent, numid, event):
        try:
            x = int(event[0])
            y = int(event[1])
            self.coordonnee.append([x, y])

            print(f"[Palette] Coordonnée ajoutée : ({x}, {y})")
            print(f"[Palette] Liste actuelle : {self.coordonnee}")

        except Exception as e:
            print("[Palette] Erreur parsing coordonnées :", e)



Moteur=Moteur("Moteur")

