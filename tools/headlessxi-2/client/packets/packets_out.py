
from common import *
from .MapPacket import *
from .packets import *

class ClientPacketsOut(object):
    def get_packet_code(self, packet):
        return util.unpack_uint32(packet, 8)

    def get_client_ver(self):
        with open(os.path.join(config.source_dir, 'settings/default/login.lua')) as f:
            settings_file = f.read()
            client_str = re.search(r'CLIENT_VER = "(.*?)"', settings_file)[1]
        return client_str

    def send_map_packet(self, data):
        self.out_packet_queue.append( (self.map_socket.conn, data) )

    def zone_login(self, charid):
        payload = bytearray(2*0x2E)
        util.memcpy(util.pack_32(charid), 0, payload, 0x0C, 4)
        return MapPacket.packet_header(0x0A, payload)

    def char_info_request(self):
        return MapPacket.packet_header(0x0C, bytearray(12))

    def dezone_confirm(self):
        payload = bytearray(8)
        return MapPacket.packet_header(0x0D, payload)

    def player_info_request(self):
        return MapPacket.packet_header(0x0F, bytearray(36))

    def zone_confirm(self):
        return MapPacket.packet_header(0x11, bytearray(8))

    def player_sync(self, client):
        payload = bytearray(2*0x10)
        util.assign( util.pack_float(client.char.x), payload, 0x04)
        util.assign( util.pack_float(client.char.y), payload, 0x08)
        util.assign( util.pack_float(client.char.z), payload, 0x0C)
        payload[0x12:0x14] = [0,0] #TODO: correct value
        payload[0x14] = client.char.rot
        util.assign( util.pack_16(client.char.target_id), payload, 0x16)
        return MapPacket.packet_header(0x15, payload)

    def player_action(self, code):
        payload = bytearray(2*0x0E)
        payload[0x0A] = code
        return payload

    def player_action_engage(self, entity):
        payload = self.player_action(0x02)
        util.assign( util.pack_16(entity.target_id), payload, 0x08)
        return MapPacket.packet_header(0x1A, payload)

    def player_action_homepoint(self):
        return MapPacket.packet_header(0x1A, self.player_action(0x0B) )

    def gear_change(self, loc, equip_slot):
        payload = bytearray(2*0x04)
        payload[0x04] = loc[1]
        payload[0x05] = equip_slot
        payload[0x06] = loc[0]
        return MapPacket.packet_header(0x50, payload)

    def command_heal(self):
        payload = bytearray(2*0x04)
        return MapPacket.packet_header(0xE8, payload)

    def command_check(self, entity):
        payload = bytearray(2*0x08)
        util.assign( util.pack_32(entity.id), payload, 0x04 )
        util.assign( util.pack_16(entity.target_id), payload, 0x08 )
        return MapPacket.packet_header(0xDD, payload)

    def request_zone(self, zoneline_id):
        payload = bytearray(2*0x0C)
        util.assign( util.pack_32(zoneline_id), payload, 0x04)
        return MapPacket.packet_header(0x5E, payload)

    def to_point_path_request(self, p):
        payload = bytearray(20)
        util.assign( util.pack_16(1003), payload, 0x04)
        util.assign( util.pack_float(p.x), payload, 0x06)
        util.assign( util.pack_float(p.y), payload, 0x0A)
        util.assign( util.pack_float(p.z), payload, 0x0E)
        return MapPacket.packet_header(0x182, payload)

    def random_path_request(self, p, max_dist, turns):
        payload = bytearray(28)
        util.assign( util.pack_16(3432), payload, 0x04)
        util.assign( util.pack_float(p.x), payload, 0x06)
        util.assign( util.pack_float(p.y), payload, 0x0A)
        util.assign( util.pack_float(p.z), payload, 0x0E)
        util.assign( util.pack_float(max_dist), payload, 0x12)
        payload[0x16] = turns
        return MapPacket.packet_header(0x182, payload)