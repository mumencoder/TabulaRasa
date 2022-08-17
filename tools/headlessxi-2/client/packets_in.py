
from common import *

import config
from packets import *
import util

class ClientPacketsIn(object):
    def init_packets_in(self):
        self.add_packet_watcher("0x8", self.react_nothing) # zone_visited
        self.add_packet_watcher("0xa", self.react_zone_in) # zone_in
        self.add_packet_watcher("0xb", self.react_server_ip) # server_ip
        self.add_packet_watcher("0xe", self.react_entity_update) # entity_update
        self.add_packet_watcher("0x1b", self.react_nothing) # char_jobs
        self.add_packet_watcher("0x1c", self.react_inventory_size) # inventory_size
        self.add_packet_watcher("0x1d", self.react_nothing) # inventory_finish
        self.add_packet_watcher("0x1f", self.react_nothing) # inventory_assign
        self.add_packet_watcher("0x20", self.react_inventory_item) # inventory_item
        self.add_packet_watcher("0x37", self.react_nothing) # char_update
        self.add_packet_watcher("0x41", self.react_downloading_data_end) # stop_downloading
        self.add_packet_watcher("0x4f", self.react_downloading_data_start) # downloading_data
        self.add_packet_watcher("0x50", self.react_char_equip) # char_equip
        self.add_packet_watcher("0x51", self.react_nothing) # char_appearance
        self.add_packet_watcher("0x55", self.react_nothing) # key_items
        self.add_packet_watcher("0x56", self.react_nothing) # quest_mission_log
        self.add_packet_watcher("0x61", self.react_nothing) # char_stats
        self.add_packet_watcher("0x67", self.react_nothing) # char_sync
        self.add_packet_watcher("0x8c", self.react_nothing) # merit_points_categories
        self.add_packet_watcher("0xaa", self.react_nothing) # char_spells
        self.add_packet_watcher("0xac", self.react_nothing) # char_abilities
        self.add_packet_watcher("0xae", self.react_nothing) # char_mounts
        self.add_packet_watcher("0xb4", self.react_nothing) # menu_config
        self.add_packet_watcher("0xca", self.react_nothing) # bazaar_message
        self.add_packet_watcher("0xd2", self.react_nothing) # treasure_find_item
        self.add_packet_watcher("0xdf", self.react_char_health) # char_health
        self.add_packet_watcher("0x182", self.react_pathfind) # pathfind

    def do_next_packet(self):
        if len(self.in_packet_queue) > 0:
            self.current_packet = self.in_packet_queue[0]
            self.in_packet_queue.popleft()
            self.process_packet(self.current_packet)

    def add_packet_watcher(self, ty, action):
        if ty not in self.packet_watchers:
            self.packet_watchers[ty] = [action]
        else:
            self.packet_watchers[ty].append( action )

    def process_packet(self, packet):
        if packet["type"] not in self.packet_watchers:
            print(f"unprocessed packet\n{packet}")
        else:
            for watcher in self.packet_watchers[packet["type"]]:
                watcher(packet["data"])

    @staticmethod
    def parseXYZLocation(packet,offset):
        return {"x": util.unpack_float(packet, offset), "y": util.unpack_float(packet, offset+4), "z": util.unpack_float(packet, offset+8) }

    @staticmethod
    def parseRXYZLocation(packet, offset):
        ret = {"rot":packet[offset]}
        ret.update(ClientPacketsIn.parseXYZLocation(packet, offset+1))
        return ret

    @staticmethod
    def parseSpeed(packet, offset):
        return {"speed":packet[offset], "subspeed":packet[offset+1] }

    @staticmethod
    def parseStats(packet, offset):
        offset = 0
        stats = {}
        for stat in ["str", "dex", "vit", "agi", "int", "mnd", "chr"]:
            stats[stat] = packet[offset]
            stats[stat + "plus"] = packet[offset+1]
            offset += 2
        return stats

    # TODO: not relative
    def parseCharHealth(self, packet, offset):
        return {
            "hp":util.unpack_uint32(packet, offset+8), "mp":util.unpack_uint32(packet, offset+0x0C), "tp":util.unpack_uint32(packet, offset+0x10),
            "hpp":util.unpack_uint32(packet, offset+0x16), "mpp":util.unpack_uint32(packet, offset+0x17) 
        }

    def react_nothing(self, packet):
        pass

    def react_downloading_data_start(self, packet):
        print("DOWNLOADING...")
        self.state.is_downloading = True

    def react_downloading_data_end(self, packet):
        print("Download finished!")
        self.state.is_downloading = False

    def react_zone_in(self, packet):
        char_id = util.unpack_uint32(packet, 0x04)
        if char_id != self.current_char["charID"]:
            raise Exception("unexpected char_id")

        self.char.updateLocation( **self.parseRXYZLocation(packet, 0x0B) )
        self.char.updateSpeed( **self.parseSpeed(packet, 0x1C) )
        self.char.updateHpp( packet[0x1E] )
        self.char.updateZone( util.unpack_uint16(packet, 0x30) )

        # TODO: moghouse
        if packet[0x80] != 2:
            raise Exception("moghouse not supported")

        self.char.updateMJob( packet[0xB4] )
        self.char.updateSJob( packet[0xB7] )
        self.char.updateStats( **self.parseStats(packet, 0xCC) )

        self.send_map_packet( self.Client.zone_confirm() )
        self.send_map_packet( self.Client.char_info_request() )
        self.send_map_packet( self.Client.player_info_request() )
        self.add_timer("sync", action=self.player_sync, interval=0.4)
        self.state.zoned_confirm = True

    def react_server_ip(self, packet):
        zone_ip = util.unpack_ip( packet, 0x08 )
        zone_port = util.unpack_uint16(packet, 0x0C )
        self.zone_ip = zone_ip
        self.zone_port = zone_port
        self.add_task( self.dezone_confirm() )
        self.add_task( self.enter_zone() )

    def react_char_equip(self, packet):
        self.char.updateEquipWorn( packet[0x04], packet[0x05], packet[0x06] ) 

    def react_char_abilities(self, packet):
        pass

    def react_char_health(self, packet):
        char_id = util.unpack_uint32(packet, 4)
        if char_id == self.current_char["charID"]:
            self.char.updateHealth( **self.parseCharHealth(packet, 0) )
        else:
            self.getChar( char_id ).updateHealth( **self.parseCharHealth(packet, 0) )

    def react_inventory_item(self, packet):
        loc = (packet[0x0E], packet[0x0F])
        item = {"id": util.unpack_uint16(packet, 0x0C), "quantity": util.unpack_uint32(packet, 0x04) }
        self.char.updateInventory( loc, item )

    def react_entity_update(self, packet):
        entity_id = util.unpack_uint32(packet, 4)
        #TODO: entity tracking

    def react_inventory_size(self, packet):
        self.char.updateInventorySize( "inv", packet[0x24] )
        self.char.updateInventorySize( "satchel", packet[0x2E] )

    def react_pathfind(self, packet):
        self.char.state.last_loc_update = time.time()
        pts = util.unpack_uint16(packet, 0x04)
        offset = 0x06
        for i in range(0,pts):
            loc = self.parseXYZLocation(packet, offset)
            destination = Point.from_dict(loc)
            if destination.x == 0.0 or destination.y == 0.0 or destination.z == 0.0:
                self.goals[-1].pathfind_failed = True
                return
            if self.dist( self.char.get_point(), destination) > 3:
                self.goals[-1].move_destination = destination
                return
            offset += 12
