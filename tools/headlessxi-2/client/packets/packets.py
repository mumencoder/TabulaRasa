
from common import *

class AsyncConnection(object):
    def __init__(self, name):
        self.name = name
        self.reader = None
        self.writer = None

    async def open(self, host=None, port=None, local_addr=None):
        (self.reader, self.writer) = await asyncio.open_connection(host=host, port=port, local_addr=local_addr)

    async def write_now(self, data):
        self.writer.write( data )
        await self.writer.drain()

    async def request_and_wait(self, data):
        await self.write_now(data)
        response = await self.reader.read(-1)
        return response

    async def write_with_response(self, packet, read_response):
        await self.write_now(packet)
        response = await read_response( self.reader )
        return response

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

def pprint_packet(bs):
    offset = 0
    result = b""
    while offset < len(bs):
        result += binascii.hexlify( bs[offset:offset+8] )
        result += b" "
        offset += 8
    return result

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

