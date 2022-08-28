
from .packets import *

class MapPacket(object):
    FFXI_HEADER_SIZE = 0x1C
    order = 1

    s2c = load_packet_types('./resources/s2c.txt')
    c2s = load_packet_types('./resources/c2s.txt')

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
        data = bytearray(28 + len(payload) + 4 + 16)
        MapPacket.order = (MapPacket.order + 1) % 65000
        util.memcpy(util.pack_16(MapPacket.order), 0, data, 0, 2)
        util.memcpy(util.pack_16(packet_id), 0, payload, 0, 2)
        if len(payload) % 4 != 0:
            raise Exception("packet not multiple of 4")
        payload[1] = (len(payload) & 0xFD) >> 1
        if packet_id > 255:
            payload[1] += 1
        util.memcpy(util.pack_16(MapPacket.order), 0, payload, 2, 2)
        util.memcpy(payload, 0, data, MapPacket.FFXI_HEADER_SIZE, len(payload))
        util.memcpy(b'\x00\x00\x00\x00', 0, data, MapPacket.FFXI_HEADER_SIZE + len(payload), 4)
        MapPacket.packet_md5(data)
        return data

    def packet_md5(data):
        to_md5 = bytearray(len(data) - (MapPacket.FFXI_HEADER_SIZE + 16))
        util.memcpy(data, MapPacket.FFXI_HEADER_SIZE, to_md5, 0, len(to_md5))
        to_md5 = hashlib.md5(to_md5)
        util.memcpy(to_md5.digest(), 0, data, len(data) - 16, 16)