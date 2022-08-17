
from common import *

import config
from packets import *
import util

class ClientPacketsOut(object):
    def send_map_packet(self, data):
        self.map_socket.conn.sendto( data )

    def create_auth_login_packet(self, command):
        data = bytearray(33)
        name = self.account["name"].encode('ascii')
        passwd = self.account["pass"].encode('ascii')
        util.memcpy(name, 0, data, 0, len(name))
        util.memcpy(passwd, 0, data, 16, len(passwd))
        data[32] = command
        return data

    def create_data_ready_packet(self):
        data = bytearray.fromhex('A10000010000000000')
        return data

    def create_data_account_packet(self, acct_id):
        data = bytearray(9)
        data[0] = 0xA1
        util.memcpy(util.pack_32(self.account_id), 0, data, 1, 4)
        return data

    def create_data_char_login_packet(self, encrypt=False):
        data = bytearray(25)
        data[0] = 0xa2 if encrypt else 0xa3
        util.memcpy(self.send_key, 0, data, 1, 20)
        return data

    def create_view_header(self, size):
        data = bytearray(size)
        util.memcpy( util.pack_32(size), 0, data, 0, 4 )
        data[4:8] = b'IXFF'
        return data

    def create_view_char_check_creation_packet(self, name):
        data = self.create_view_header(48)
        data[8] = 0x22
        util.memcpy(util.pack_str(name), 0, data, 32, 16)
        return data

    def create_view_char_creation_packet(self):
        data = self.create_view_header(64)
        data[8] = 0x21
        data[48] = 7 # race
        data[50] = random.randint(0, 6)
        data[54] = 2
        data[57] = random.randint(0, 2) # size
        data[60] = random.randint(0, 15) # face
        return data

    def create_view_clientver_packet(self):
        data = self.create_view_header(152)
        data[8] = 0x26
        util.memcpy(util.pack_str(self.client_ver), 0, data, 116, 10)
        return data

    def create_view_ready_packet(self):
        data = self.create_view_header(44)
        data[8] = 0x1F
        return data

    def create_view_get_server_name_packet(self):
        data = self.create_view_header(16)
        data[8] = 0x24
        return data

    def create_view_char_login_choice_packet(self, char_entry):
        data = self.create_view_header(88)
        data[8] = 0x07
        util.memcpy(util.pack_32(char_entry["charID"]), 0, data, 0x1C, 4)
        return data    

    class Client(object):
        def zone_login(charid):
            payload = bytearray(2*0x2E)
            util.memcpy(util.pack_32(charid), 0, payload, 12, 4)
            return MapPacket.packet_header(0x0A, payload)

        def zone_confirm():
            return MapPacket.packet_header(0x11, bytearray(8))

        def char_info_request():
            return MapPacket.packet_header(0x0C, bytearray(12))

        def dezone_confirm():
            payload = bytearray(8)
            return MapPacket.packet_header(0x0D, payload)

        def player_info_request():
            return MapPacket.packet_header(0x0F, bytearray(36))

        def player_sync(client):
            payload = bytearray(2*0x10)
            util.assign( util.pack_float(client.char.x), payload, 0x04)
            util.assign( util.pack_float(client.char.y), payload, 0x08)
            util.assign( util.pack_float(client.char.z), payload, 0x0C)
            payload[0x12:0x14] = [0,0] #TODO: correct value
            payload[0x14] = client.char.rot
            util.assign( util.pack_16(client.char.target_id), payload, 0x16)
            return MapPacket.packet_header(0x15, payload)

        def request_zone(zoneline_id):
            payload = bytearray(2*0x0C)
            util.assign( util.pack_32(zoneline_id), payload, 0x04)
            return MapPacket.packet_header(0x5E, payload)

        def path_request(p):
            payload = bytearray(16)
            util.assign( util.pack_float(p.x), payload, 0x04)
            util.assign( util.pack_float(p.y), payload, 0x08)
            util.assign( util.pack_float(p.z), payload, 0x0C)
            return MapPacket.packet_header(0x182, payload)
