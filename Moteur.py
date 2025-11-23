import time
from datetime import datetime
from ivy.ivy import IvyServer

class Moteur(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, name)
        print("start")
        self.start('127.255.255.255:2010')
        self.bind_msg(self.handle_msg_vocal, "sra5 Parsed=action=(.*) where=(.*) form=(.*) color=(.*) localisation=(.*) Confidence=(.*) NP=.* Num_A=.*")
        self.bind_msg(self.handle_msg_geste,"NDOLLAR_RECO name=(.*) score=(.*)")
        self.bind_msg(self.handle_msg_palette, r"Palette Click couleur=(.*) x=(.*) y=(.*)")

        self.bind_msg(
            lambda agent, *groups: print("[BUS MESSAGE]", repr(groups), "AGENT:", agent),
            "(.*)"
        )

        self.name = name
        self.where=""
        self.action = ""
        self.forme = ""
        self.couleur = ""
        self.localisation =""
        self.coordonnees = []
        self.nbModalitees=0

        self.timer=None

        self.SEUIL_FUSION=2
        self.SEUIL_ABANDON=5

    def update_timer(self):
         self.timer= datetime.now()


    def fusion(self):
        if self.timer is None:
            return

        elapsed = (datetime.now()- self.timer).total_seconds()

        if elapsed > self.SEUIL_ABANDON:
            self.where = ""
            self.action = ""
            self.forme = ""
            self.couleur = ""
            self.localisation = ""
            self.coordonnees = []
            self.nbModalitees=0

            self.timer = None

        elif (elapsed > self.SEUIL_FUSION and ( (self.action == "CREATE" and self.nbModalitees > 1 and self.forme != "")
        or (self.action == "DELETE" and (self.forme != "" or self.couleur != "") )
        or (self.action == "MOVE" and ( len(self.coordonnees) > 1 or self.forme != "" or self.couleur != "")))):

            if not self.coordonnees:
                self.coordonnees=[200,200]
            self.send_msg(f"FUSION: ACTION={self.action} WHERE={self.where} FORME={self.forme} COULEUR={self.couleur} "
                          f"LOCALISATION={self.localisation} COORDONNES={self.coordonnees}")
            print(self.nbModalitees)

            self.timer = None
            self.where = ""
            self.action = ""
            self.forme = ""
            self.couleur = ""
            self.localisation = ""
            self.coordonnees = []
            self.nbModalitees = 0



    def handle_msg_vocal(self, agent, action, where, form, color, localisation, confidence):
        if float(confidence.replace(",", ".")) > 0.70:
            self.action = action
            self.where = where
            if self.forme=="":
                self.forme = form
            if self.couleur=="":
                self.couleur = color
            self.localisation = localisation
            self.nbModalitees += 1
            self.update_timer()
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")

    def handle_msg_geste(self, agent, form, confidence):
        print(confidence)
        if float(confidence) > 0.50:
            self.forme = form
            self.nbModalitees += 1
            self.update_timer()
            print(form)
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")

    def handle_msg_palette(self, agent, couleur, x, y):
        try:
            x = int(x)
            y = int(y)
            self.coordonnees.append([x, y])
            if couleur!="undefined":
                self.couleur=couleur
            self.nbModalitees += 1
            self.update_timer()

            print(f"[Palette] Coordonnée ajoutée : ({x}, {y})")
            print(f"[Palette] Liste actuelle : {self.coordonnees}")

        except Exception as e:
            print("[Palette] Erreur parsing coordonnées :", e)



Moteur=Moteur("Moteur")
while True:
    Moteur.fusion()
    time.sleep(0.05)
