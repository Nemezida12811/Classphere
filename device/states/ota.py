from states.state import AbstractState

from states.sleep import Sleep


class OTA(AbstractState):
    def enter(self):
        print('>> OTA State...')
    
    
    def exec(self):       
        
       
       
    def exit(self):
        print('>> Exit from OTA state.')

