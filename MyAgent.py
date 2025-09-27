from ivy.ivy import IvyServer
class MyAgent(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, "IvyServer")
        self.name = name
        self.start('127.0.0.1:2010')
        self.bind_msg(self.handle_msg, "sra5 Text=(.*) Confidence=(.*)")
        print("here")

    def handle_msg(self, agent, numid, texte, confidence):
        #print(f"[Agent {self.name}] got Text={texte} with Confidence={confidence}, from {agent}")
        if float(confidence.replace(",", "."))>0.50:
            self.send_msg(f"ppilot5 Say=vous avez dit :{texte}")
        else:
            self.send_msg(f"ppilot5 Say=Je n'ai pas compris")
a= MyAgent("MyAgent")