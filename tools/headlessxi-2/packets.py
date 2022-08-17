
from common import *
import util

class ParsedPacket(object):
    def __init__(self, packet):
        self.packet = packet
        self.parsed = []
        self.marks = []

    def add(self, start, size, **kwargs):
        self.marks.append( (start,start+size) )
        self.parsed.append( kwargs )

    def finalize(self):
        self.compute_unknown()
        self.full_packet = binascii.hexlify( self.packet )

    def compute_unknown(self):
        result = b""
        self.all_known = True
        for i in range(0, len(self.packet)):
            known = False
            for mark in self.marks:
                if i >= mark[0] and i < mark[1]:
                    known = True
            if known:
                result += b'__'
            if not known:
                self.all_known = False
                result += binascii.hexlify( self.packet[i:i+1] )
        self.unknown_str = result

def parse_lobby_data_s2c(packet):
    ppacket = ParsedPacket(packet)

    if packet[0] == 1:
        pass
        #ppacket.add(0, 1, code=1, desc="lobby ready")
    if packet[0] == 3:
        pass
        #ppacket.add(0, 1, code=3, desc="content ID updates")

    ppacket.finalize()
    return ppacket

def parse_lobby_data_c2s(packet):
    ppacket = ParsedPacket(packet)
    if packet[0] == 0xA1:
        #ppacket.add(0, 1, code=0xA1, desc="lobby data client init")
        ppacket.add(5, 4, server_ip=util.unpack_ip(packet, 5) )
    ppacket.finalize()
    return ppacket

def parse_lobby_view_s2c(packet):
    ppacket = ParsedPacket(packet)

    size = util.unpack_uint32(packet, 0)
    if size > 4096:
        raise Exception("bad view response size")
    if util.unpack_str(packet, 4, 4) != 'IXFF':
        raise Exception("bad view response header", util.unpack_str(packet, 4, 4))
    ppacket.add(0, 4, packet_size=size)
    ppacket.add(4, 4)
    ppacket.add(12, 16, hash=util.unpack_binary(packet, 12, 16))

    if packet[8] == 5:
        ppacket.add(32, 4, expansion_flags=util.unpack_uint32(packet, 32))
        ppacket.add(36, 4, feature_flags=util.unpack_uint32(packet, 36))

    ppacket.finalize()
    return ppacket

def parse_lobby_view_c2s(packet):
    ppacket = ParsedPacket(packet)

    size = util.unpack_uint32(packet, 0)
    if size > 4096:
        raise Exception("bad view response size")
    if util.unpack_str(packet, 4, 4) != 'IXFF':
        raise Exception("bad view response header", util.unpack_str(packet, 4, 4))
    ppacket.add(0, 4, packet_size=size)
    ppacket.add(4, 4)
    ppacket.add(12, 16, hash=util.unpack_binary(packet, 12, 16))

    if packet[8] == 0x26:
        ppacket.add(0x74, 10, client_version=util.unpack_str(packet, 0x74, 10))

    ppacket.finalize()
    return ppacket

def load_packet_types(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    state = "readid"
    descs = []
    packet_type = None
    results = {}
    for line in lines:
        if state in ["readid","readmsg"] and line.startswith('0x'):
            if packet_type is not None:
                results[packet_type] = {"descs":descs}
                descs = []
            split = line.split("-")
            packet_type = int(split[0].strip(" "), base=16)
            descs.append( split[1].strip("\n") )
            state = "readmsg"
        elif state == "readmsg" and not line.startswith('0x'):
            descs.append( line.strip("\t").strip(" ") )
        else:
            raise Exception("unknown state transition")
    return results

class MapPacket(object):
    FFXI_HEADER_SIZE = 0x1C
    order = 1

    s2c = load_packet_types('./util/s2c.txt')
    c2s = load_packet_types('./util/c2s.txt')

    def parse_large_packet(data):
        offset = MapPacket.FFXI_HEADER_SIZE
        packets = []
        while offset < len(data) - 16:
            typesize = util.unpack_uint16( data, offset )
            packet_type = typesize & 0x1FF
            packet_size = 2 * ((typesize & 0xFE00) >> 8)
            packet_payload = data[offset:offset+packet_size]
            if packet_size < 1 or packet_size > 1500:
                raise Exception("rejected packet", packet_type, packet_size)
            offset += packet_size
            spacket = {"type":hex(packet_type), "size":packet_size, "data":packet_payload}
            packets.append( spacket )
        return packets

    def packet_header(packet_id, payload):
        data = bytearray(28 + len(payload) + 16)
        MapPacket.order += 1
        util.memcpy(util.pack_16(MapPacket.order), 0, data, 0, 2)
        util.memcpy(util.pack_16(packet_id), 0, payload, 0, 2)
        if len(payload) % 4 != 0:
            print("packet not multiple of 4")
        payload[1] = (len(payload) & 0xFD) >> 1
        if packet_id > 255:
            payload[1] += 1
        util.memcpy(util.pack_16(MapPacket.order), 0, payload, 2, 2)
        util.memcpy(payload, 0, data, MapPacket.FFXI_HEADER_SIZE, len(payload))
        MapPacket.packet_md5(data)
        return data

    def packet_md5(data):
        to_md5 = bytearray(len(data) - (MapPacket.FFXI_HEADER_SIZE + 16))
        util.memcpy(data, MapPacket.FFXI_HEADER_SIZE, to_md5, 0, len(to_md5))
        to_md5 = hashlib.md5(to_md5)
        util.memcpy(to_md5.digest(), 0, data, len(data) - 16, 16)

def big_packet_decrypt(self, data):
    print( binascii.hexlify(data) )
    payload = data[ MapPacket.FFXI_HEADER_SIZE: ]

    blocks = int(len(payload) / 8)
    result = b""
    offset = 0
    for block in range(0, blocks):
        l = payload[offset:offset+4]
        r = payload[offset+4:offset+8]
        result += self.blowfish.decrypt_block( payload[offset:offset+8] )
        offset += 8
    result += payload[offset:]
    print( binascii.hexlify( data[0:MapPacket.FFXI_HEADER_SIZE] + result ) )

def init_blowfish(self):
    starting_key = list(self.starting_key)
    starting_key[4] += 2

    byte_array = bytearray(len(starting_key) * 4)
    util.memcpy(util.pack_32(starting_key[0]), 0, byte_array, 0, 4)
    util.memcpy(util.pack_32(starting_key[1]), 0, byte_array, 4, 4)
    util.memcpy(util.pack_32(starting_key[2]), 0, byte_array, 8, 4)
    util.memcpy(util.pack_32(starting_key[3]), 0, byte_array, 12, 4)
    util.memcpy(util.pack_32(starting_key[4]), 0, byte_array, 16, 4)

    self.send_key = bytearray(byte_array)
    if self.is_new_char:
        starting_key[4] += 6
        util.memcpy(util.pack_32(starting_key[0]), 0, byte_array, 0, 4)
        util.memcpy(util.pack_32(starting_key[1]), 0, byte_array, 4, 4)
        util.memcpy(util.pack_32(starting_key[2]), 0, byte_array, 8, 4)
        util.memcpy(util.pack_32(starting_key[3]), 0, byte_array, 12, 4)
        util.memcpy(util.pack_32(starting_key[4]), 0, byte_array, 16, 4)

    hash_key = hashlib.md5(byte_array).digest()

    for i in range(16):
        if hash_key[i] == 0:
            zero = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            memcpy(zero, i, hash_key, i, 16 - i)

    self.final_key = hash_key
    print( 'hash', binascii.hexlify(self.final_key) )
    return blowfish.Cipher(hash_key)