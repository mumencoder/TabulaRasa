
class ZoneMap(object):
    class Division(object):
        def __init__(self, div, new_block):
            self.div = div
            self.blocks = collections.defaultdict(new_block)

        def get_block_key(self, p):
            block_x = int(p.x / div)
            block_z = int(p.z / div)
            return (block_x, block_z)

        def get_block(self, p):
            key = self.get_block_key(p)
            return self.blocks[key]

    def __init__(self):
        self.id = None
        self.entity_locs = collections.defaultdict(set)
        self.entity_lvls = collections.defaultdict(set)

