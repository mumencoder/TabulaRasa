
from common import *

class Point(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_dict(d):
        return Point(d["x"], d["y"], d["z"])

    def __str__(self):
        return f"x={self.x} y={self.y} z={self.z}"

    def direction(p1, p2):
        return Point.norm( Point.sub(p1, p2) )

    def neg(p):
        return Point( -p.x, -p.y, -p.z )

    def smul(s, p):
        return Point( s*p.x, s*p.y, s*p.z )

    def add(p1, p2):
        return Point( p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

    def sub(p1, p2):
        return Point( p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)

    def nav_dist(p1, p2):
        if abs(p1.y - p2.y) < 3:
            return math.sqrt( (p1.x-p2.x)**2 + (p1.z-p2.z)**2 )
        else:
            return Point.dist(p1, p2)

    def dist(p1, p2):
        return math.sqrt( (p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2 )

    def norm(p):
        if p.x == 0.0 and p.y == 0.0 and p.z == 0.0:
            return p
        N = Point.dist(p, Point(0.0, 0.0, 0.0))
        return Point( p.x / N, p.y / N, p.z / N)

    def rad_to_rot(rad):
        if rad >= 0:
            return int( (rad * (128 / math.pi) - 64) % 256 ) 
        if rad < 0:
            return int( (256 - abs(rad) * (128 / math.pi) - 64) % 256 )

    def lookat(looker, lookee):
        d = Point.direction(lookee, looker)
        return Point.rad_to_rot( math.atan2(d.x, d.z) )