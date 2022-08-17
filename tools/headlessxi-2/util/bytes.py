
import struct

def unpack_uint16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]

def unpack_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def unpack_uint32_nb(data, offset):
    return struct.unpack_from('>I', data, offset)[0]

def unpack_float(data, offset):
    return struct.unpack_from('<f', data, offset)[0]
    
def unpack_str(data, offset, size):
    end_offset = offset
    while data[end_offset] != 0 and end_offset-offset < size:
        end_offset += 1
    return data[offset:end_offset].decode('utf-8')

def unpack_binary(data, offset, size):
    return data[offset:offset+size]

def unpack_ip(data, offset):
    s = ""
    for i in range(0,4):
        s += str(data[offset+i]) + '.'
    return s[0:-1]

def pack_16(data):
    return struct.pack('<H', data)

def pack_32(data):
    return struct.pack('<I', data)

def pack_float(data):
    return struct.pack('<f', data)

def pack_str(data):
    return data.encode('utf-8') 

def assign(src, dst, dst_offset):
    memcpy(src, 0, dst, dst_offset, len(src))

def memcpy(src, src_offset, dst, dst_offset, count):
    if len(src) < count:
        count = len(src)
    src_bytes = src[src_offset:src_offset+count]
    dst[dst_offset:dst_offset+count] = src_bytes