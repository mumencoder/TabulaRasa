
from common import *

print( util.unpack_bits(b'\x00', 0, 8) == 0)
print( util.unpack_bits(b'\x00', 0, 9) == None)
print( util.unpack_bits(b'\x02', 1, 2) == 1)
print( util.unpack_bits(b'\x06', 1, 2) == 3)
print( util.unpack_bits(b'\x80\x01', 7, 2) == 3) 
