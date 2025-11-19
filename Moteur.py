from ivy.ivy import IvyServer
class Moteur(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, name)
        print("start")
        self.start('127.0.0.1:2010')
        self.bind_msg(self.handle_msg_vocal, "sra5 Parsed=action=(.*) where=(.*) form=(.*) color=(.*) localisation=(.*) Confidence=(.*) NP=.* Num_A=.*")
        self.bind_msg(self.handle_msg_geste,"NDOLLAR_RECO name=(.*) score=(.*)")
        self.bind_msg(
            lambda agent, *groups: print("[BUS MESSAGE]", repr(groups), "AGENT:", agent),
            "(.*)"
        )

        self.name = name
        self.action = ""
        self.forme = ""
        self.couleur = ""
        self.localisation = []

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


Moteur=Moteur("Moteur")

