
from common import *

import config
import util

class HXIClient(object):
    def __init__(self, account, server_host, client_ver=''):
        self.account = account
        self.server_host = server_host

        self.tasks = collections.deque()

        self.connected = False

        if client_ver == '':
            self.client_ver = self.get_client_ver()
        else:
            self.client_ver = "30220705_0" 

        self.blowfish = self.init_blowfish()

        self.tasks.append( {"action":self.do_account_login} )

    async def update(self):
        self.state = self.tasks[0]
        self.tasks.popleft()
        await self.state["action"](self)

    def create_login_packet(self, command):
        data = bytearray(33)
        name = self.account["name"].encode('ascii')
        passwd = self.account["pass"].encode('ascii')
        util.memcpy(name, 0, data, 0, len(name))
        util.memcpy(passwd, 0, data, 16, len(passwd))
        data[32] = command
        return data

    def create_data_account_packet(self, acct_id):
        data = bytearray(5)
        data[0] = 0xA1
        util.memcpy(util.pack_32(self.account_id), 0, data, 1, 4)
        return data

    def create_view_char_check_creation_packet(self, name):
        data = bytearray(48)
        data[8] = 0x22
        util.memcpy(util.pack_str(name), 0, data, 32, 16)
        return data

    def create_view_char_creation_packet(self):
        data = bytearray(64)
        data[8] = 0x21
        data[48] = 7 # race
        data[50] = random.randint(0, 6)
        data[54] = 2
        data[57] = random.randint(0, 2) # size
        data[60] = random.randint(0, 15) # face
        return data

    def create_view_clientver_packet(self):
        data = bytearray(152)
        data[8] = 0x26
        util.memcpy(util.pack_str(self.client_ver), 0, data, 116, 10)
        return data

    def create_view_ready_packet(self):
        data = bytearray(44)
        data[8] = 0x1F
        return data

    def create_view_get_server_name_packet(self):
        data = bytearray(16)
        data[8] = 0x24
        return data

    def create_view_idk(self):
        data = bytearray(16)
        data[8] = 0x07
        return data

    def create_data_ready_packet(self):
        data = bytearray.fromhex('A10000010000000000')
        return data

    @staticmethod
    async def do_account_login(self):
        (self.login_reader, self.login_writer) = await asyncio.open_connection(host=self.server_host, port=config.login_port)

        data = self.login_writer.write( self.create_login_packet( 0x10 ) )
        await self.login_writer.drain()
        response = await self.login_reader.read(-1)
        print("login response", response)
        if response[0] == 1:
            self.account_id = util.unpack_uint16(response, 1)
            self.tasks.append( {"action":self.enter_lobby} )
        elif response[0] == 2:
            self.tasks.append( {"action":self.create_account} )
            return
        else: 
            raise Exception("unknown response code", response)


    @staticmethod
    async def create_account(self):
        (self.login_reader, self.login_writer) = await asyncio.open_connection(host=self.server_host, port=config.login_port)

        data = self.login_writer.write( self.create_login_packet( 0x20 ) )
        await self.login_writer.drain()
        response = await self.login_reader.read(-1)
        if response[0] == 3:
            self.tasks.append( {"action":self.do_account_login} )
        else:
            raise Exception("unknown response code", response)

    async def read_sizeheader_packet(self, stream):
        sizebytes = await stream.readexactly(4)
        size = util.unpack_uint32(sizebytes, 0)
        if size > 4096:
            raise Exception("bad view response size")
        response = await stream.readexactly(size - 4)
        if util.unpack_str(response, 0, 4) != 'IXFF':
            raise Exception("bad view response header", util.unpack_str(response, 0, 4))
        return sizebytes + response

    async def refresh_lobby(self):
        self.view_writer.write( self.create_view_ready_packet() )
        await self.view_writer.drain()

        self.data_writer.write( self.create_data_ready_packet() )
        await self.data_writer.drain()
        data_response = await self.data_reader.readexactly(5)

        # this appears broken/useless
        data_response = await self.data_reader.readexactly(328)
        view_response = await self.read_sizeheader_packet( self.view_reader )

        char_names = []
        hasChars = True
        i = 0
        while hasChars:
            charListOffset = 32 + i * 140
            if charListOffset + 78 > len(view_response):
                hasChars = False
                continue
            contentId = util.unpack_uint32(view_response, charListOffset )
            if contentId != 0:
                char_names.append( util.unpack_str(view_response, charListOffset+12, 16) )
            i += 1

        return char_names

    @staticmethod
    async def enter_lobby(self):
        (self.data_reader, self.data_writer) = await asyncio.open_connection(host=self.server_host, port=config.data_port)
        (self.view_reader, self.view_writer) = await asyncio.open_connection(host=self.server_host, port=config.view_port)
        self.data_writer.write( self.create_data_account_packet(self.account_id) )
        await self.data_writer.drain()
        data_response = await self.data_reader.readexactly(5)

        self.view_writer.write( self.create_view_clientver_packet() )
        await self.view_writer.drain()
        response = await self.view_reader.readexactly(40)
        self.expansion_bitmask = util.unpack_uint32(response, 32)
        self.feature_bitmask = util.unpack_uint32(response, 36)

        self.char_names = await self.refresh_lobby()

        self.tasks.append( {"action":self.login_char} )

    @staticmethod
    async def login_char(self):
        if len(self.char_names) == 0:
            charname = self.account["char_names"][0]
            print("creating char", charname)
            print( self.create_view_char_check_creation_packet(charname) )
            self.view_writer.write( self.create_view_char_check_creation_packet(charname) )
            await self.view_writer.drain()

            response = await self.read_sizeheader_packet( self.view_reader )
            if response[8] == 3:
                print("character OK")
                self.view_writer.write( self.create_view_char_creation_packet() )
                response = await self.read_sizeheader_packet( self.view_reader )
            login_char = charname
        else:
            if char_names[0] not in self.account["char_names"]:
                raise Exception("unknown char")
            login_char = char_names[0]
            
        self.view_writer.write( self.create_view_get_server_name_packet() )
        await self.view_writer.drain()
        response = await self.read_sizeheader_packet( self.view_reader )
        self.server_name = util.unpack_str( response, 36, 16)

    def get_client_ver(self):
        with open(os.path.join(config.source_dir, 'settings/default/login.lua')) as f:
            settings_file = f.read()
            client_str = re.search(r'CLIENT_VER = "(.*?)"', settings_file)[1]
        return client_str

    @staticmethod
    def init_blowfish():
        starting_key = [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0xAD5DE056]
        starting_key[4] = starting_key[4] + 2
        byte_array = bytearray(len(starting_key) * 4)

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

        return util.Blowfish(hash_key)