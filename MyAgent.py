from ivy.ivy import IvyServer
class MyAgent(IvyServer):
    def __init__(self, name):
        IvyServer.__init__(self, "IvyServer")
        self.name = name
        self.start('127.0.0.1:2010')
        self.bind_msg(self.handle_msg, "test (.*)")
        print("here")

    def handle_msg(self, agent, numid, arg):
        print(f"[Agent {self.name}] got {arg}, from {agent}")
        self.send_msg(f"ppilot5 Say=vous avez dit :{arg}")
a= MyAgent("MyAgent")