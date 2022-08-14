
class Char(object):
    def __init__(self):
        self.zone = None
        self.rot = None
        self.x = None
        self.y = None
        self.z = None
        self.hpp = None
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

    def updateAttrs( self, attrs):
        for key, value in attrs.items():
            if not hasattr(self, key):
                raise Exception("attempt to set invalid attr", key)
            setattr(self, key, value)

    def updateZone(self, zone):
        self.zone = zone

    def updateLocation( self, **kwargs ):
        self.updateAttrs(kwargs)

    def updateSpeed( self, **kwargs):
        self.updateAttrs(kwargs)

    def updateHpp( self, hpp ):
        self.hpp = hpp

    def updateStats( self, **kwargs ):
        self.updateAttrs(kwargs)

    def updateMJob( self, mjob):
        self.mjob = mjob

    def updateSJob( self, sjob):
        self.sjob = sjob