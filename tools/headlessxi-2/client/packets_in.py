
from common import *

import config
from packets import *
import util

class ClientPacketsIn(object):
    def init_packets_in(self):
        self.add_packet_watcher("0x4f", self.react_download_packet) # downloading_data
        self.add_packet_watcher("0xa", self.react_zone_in_packet) # zone_in
        self.add_packet_watcher("0x8", self.react_zone_visited_packet) # zone_visited

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
    def parseRXYZLocation(packet, offset):
        return {"rot":packet[offset], "x": util.unpack_float(packet, offset+1), "y": util.unpack_float(packet, offset+5), "z": util.unpack_float(packet, offset+9)}
    
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

    def react_download_packet(self, packet):
        self.state.is_downloading = True

    def react_zone_in_packet(self, packet):
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

        self.send_map_packet( MapPacket.Client.zone_confirm() )

    def react_zone_visited_packet(self, packet):
        pass