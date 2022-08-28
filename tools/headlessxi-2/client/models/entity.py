
class Entity(object):
    def __init__(self):
        self.target_id = None
        self.name = None
        self.loc = None
        self.hpp = None

        self.zone = None
        self.level = None
        
        self.attackable = None
        self.alive = None

    def updateHPP(self, hpp):
        if hpp > 0:
            self.alive = True
        else:
            self.alive = False
        self.hpp = hpp