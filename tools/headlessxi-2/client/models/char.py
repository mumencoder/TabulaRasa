
from common import *

class CharState(object):
    pass

class Char(object):
    def __init__(self):
        self.state = CharState()
        self.state.last_loc_update = time.time()

        self.zone = None
        self.rot = None
        self.x = None
        self.y = None
        self.z = None

        self.hp = None
        self.mp = None
        self.tp = None
        self.hpp = None
        self.mpp = None

        self.speed = None
        self.subspeed = None

        self.str = None
        self.strplus = None
        self.dex = None
        self.dexplus = None
        self.vit = None
        self.vitplus = None
        self.agi = None
        self.agiplus = None
        self.int = None
        self.intplus = None
        self.mnd = None
        self.mndplus = None
        self.chr = None
        self.chrplus = None

        self.target_id = 0

        self.equip = {}
        self.inventory = {}

        self.inventory_sizes = {}

    def get_point(self):
        return Point(self.x, self.y, self.z)

    def updateAttrs( self, attrs):
        for key, value in attrs.items():
            if not hasattr(self, key):
                raise Exception("attempt to set invalid attr", key)
            setattr(self, key, value)

    def updateZone(self, zone):
        self.zone = zone

    def updateLocation( self, **kwargs ):
        self.state.last_loc_update = time.time()
        self.updateAttrs(kwargs)

    def updateSpeed( self, **kwargs):
        self.updateAttrs(kwargs)

    def updateHealth( self, **kwargs):
        self.updateAttrs(kwargs)

    def updateHpp( self, hpp ):
        self.hpp = hpp

    def updateStats( self, **kwargs ):
        self.updateAttrs(kwargs)

    def updateMJob( self, mjob):
        self.mjob = mjob

    def updateSJob( self, sjob):
        self.sjob = sjob

    def updateEquipWorn(self, equip_slot, inv_slot, container):
        self.equip[equip_slot] = {"inv_slot":inv_slot, "container":container}

    def updateInventory(self, loc, item):
        self.inventory[loc] = item

    def updateInventorySize(self, name, size):
        self.inventory_sizes[name] = size