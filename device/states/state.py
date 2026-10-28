class AbstractState:
    def __init__(self, device):
        self.device = device
        
    def enter(self):
        pass
        
    def exec(self):
        pass
        
    def exit(self):
        pass