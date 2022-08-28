
from common import *

class CharState(object):
    pass

class Char(object):
    def __init__(self):
        self.state = CharState()
        self.state.last_loc_update = time.time()

        self.animation = None

        self.zone = None
        self.rot = None
        self.x = None
        self.y = None
        self.z = None

        self.job_unlocked = None
        self.job_levels = None

        self.mjob = None
        self.sjob = None

        self.mlvl = None
        self.slvl = None

        self.mlvls = None
        self.slvls = None

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

        self.target_id = None

        self.equip = {} # equip_slot : {"inv_slot", "container"}
        self.inventory = {} # (containerID, slotID) : {"id", "quantity"}

        self.inventory_sizes = {}

    def log(self, msg, **kwargs):
        pass
        #print(msg, kwargs)

    def get_point(self):
        return util.Point(self.x, self.y, self.z)
        
    def equipped_item(self, slot_id):
        if slot_id not in self.equip:
            return None
        loc = self.equip[slot_id]
        key =  (loc["container"], loc["inv_slot"]) 
        if key not in self.inventory:
            self.log(f"item not found", loc=key, equip=self.equip, inventory=self.inventory)
            return None
        return self.inventory[key]

    def find_item(self, item_id):
        for loc, item in self.inventory.items():
            if item["id"] == item_id:
                return loc

    def updateAttrs(self, attrs):
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