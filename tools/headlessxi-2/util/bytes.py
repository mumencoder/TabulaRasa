
import struct

def unpack_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def unpack_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def unpack_str(data, offset, size):
    end_offset = offset
    while data[end_offset] != 0 and end_offset-offset < size:
        end_offset += 1
    return data[offset:end_offset].decode('utf-8')

def pack_16(data):
    return struct.pack('<H', data)

def pack_32(data):
    return struct.pack('<I', data)

def pack_str(data):
    return data.encode('utf-8') 


def memcpy(src, src_offset, dst, dst_offset, count):
    if len(src) < count:
        count = len(src)
    src_bytes = src[src_offset:src_offset+count]
    dst[dst_offset:dst_offset+count] = src_bytes