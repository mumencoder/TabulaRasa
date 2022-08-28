
class Blowfish(object):
    def __init__(self):
        self.starting_key = [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0xAD5DE056]
        self.send_key = bytearray(0)*20

    def big_packet_decrypt(self, data):
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
        return blowfish.Cipher(hash_key)