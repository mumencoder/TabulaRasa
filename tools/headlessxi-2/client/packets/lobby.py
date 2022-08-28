
from common import *
from .packets import *
from ..goals import *

class ClientLobby(object):
    def init_lobby(self):
        if self.login_conn is not None:
            self.login_conn.close()
            self.login_conn = None

        self.lobby = Object()
        self.lobby.account_id = None
        self.lobby.expansion_bitmask = None
        self.lobby.feature_bitmask = None
        self.lobby.log = []

    def log_lobby(self, text):
        self.lobby.log.append(text)

    def create_auth_login_packet(self, command):
        data = bytearray(33)
        name = self.account.username.encode('ascii')
        passwd = self.account.password.encode('ascii')
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
        #util.memcpy(self.send_key, 0, data, 1, 20)
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
        data[50] = random.randint(1, 6) # job
        data[54] = random.randint(0, 2) # nation
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
        util.memcpy(util.pack_32(char_entry.charID), 0, data, 0x1C, 4)
        return data    

    def auth_error(self, msg):
        print("auth error", msg, self.local_host, self.account.username, self.account.password)

    async def open_auth_connection(self):
        self.login_conn = AsyncConnection("login")
        await self.login_conn.open(host=config.login_ip, port=config.login_port, local_addr=(self.local_host, random.randint(40000,48000)))

    async def open_data_connection(self):
        self.data_conn = AsyncConnection("data")
        await self.data_conn.open(host=config.data_ip, port=config.data_port, local_addr=(self.local_host, random.randint(40000,48000)))

    async def open_view_connection(self):
        self.view_conn = AsyncConnection("view")
        await self.view_conn.open(host=config.view_ip, port=config.view_port, local_addr=(self.local_host, random.randint(40000,48000)))

    async def auth_try_login(self):
        if self.login_conn is None:
            await self.open_auth_connection()
        response = await self.login_conn.request_and_wait( self.create_auth_login_packet( 0x10 ) )
        self.login_conn = None
        if response[0] == 1:
            self.account_id = util.unpack_uint16(response, 1)
            await self.auth_enter_lobby()
        elif response[0] == 2:
            await self.auth_create_account()
        else: 
            await self.auth_error("auth_try_login")

    async def auth_create_account(self):
        if self.login_conn is None:
            await self.open_auth_connection()
        response = await self.login_conn.request_and_wait( self.create_auth_login_packet( 0x20 ) )
        self.login_conn = None
        if response[0] == 3:
            await self.auth_try_login()
        else:
            self.auth_error("auth_create_account")

    async def auth_enter_lobby(self):
        if self.data_conn is None:
            await self.open_data_connection()
        if self.view_conn is None:
            await self.open_view_connection()

        data_response = await self.data_conn.reader.readexactly(5)
        if data_response[0] != 1:
            return ActionGoal( self.lobby_entry_failed )

        await self.data_conn.write_now( self.create_data_account_packet(self.account_id) )
        await self.view_conn.write_now( self.create_view_clientver_packet() )
        view_response = await self.view_conn.reader.readexactly(40)
        self.expansion_bitmask = util.unpack_uint32(view_response, 32)
        self.feature_bitmask = util.unpack_uint32(view_response, 36)
        await self.choose_login_char()

    async def refresh_lobby(self):
        await self.view_conn.write_now( self.create_view_ready_packet() )
        data_response = await self.data_conn.reader.readexactly(5)
        if data_response[0] != 1:
            raise Exception("data not ready")

        await self.data_conn.write_now( self.create_data_ready_packet() )
        data_response = await self.data_conn.reader.readexactly(328)
        view_response = await self.check_packet_sizeheader( self.view_conn.reader )

        self.lobby.char_data = []
        hasChars = True
        i = 0
        while hasChars:
            charListOffset = 32 + i * 140
            if charListOffset + 78 > len(view_response):
                hasChars = False
                continue
            char_entry = Object()
            char_entry.contentID = util.unpack_uint32(view_response, charListOffset )
            if char_entry.contentID != 0:
                char_entry.charID = util.unpack_uint16(view_response, charListOffset + 4)
                char_entry.worldID = view_response[charListOffset+6]
                char_entry.charExtra = view_response[charListOffset+11]
                char_entry.name = util.unpack_str(view_response, charListOffset+12, 16)
                self.lobby.char_data.append( char_entry )
            i += 1

    async def create_char(self):
        charname = None
        while charname is None:
            charname = random.choice( self.himi.char_names_all )
        self.log_lobby( f"creating char {charname}")
        response = await self.view_conn.write_with_response( self.create_view_char_check_creation_packet(charname), self.check_packet_sizeheader )
        if self.get_packet_code(response) == 3:
            response = await self.view_conn.write_with_response( self.create_view_char_creation_packet(), self.check_packet_sizeheader )
            if self.get_packet_code(response) != 3:
                self.log_lobby( "character creation: failed" )
                await asyncio.sleep(2.0)
                await self.create_char()
                return
            self.log_lobby( "character creation: success")
        else:
            self.log_lobby( "character creation: name not available")
            await asyncio.sleep(2.0)
            await self.create_char()

    async def choose_login_char(self):
        await self.refresh_lobby()
        response = await self.view_conn.write_with_response( self.create_view_get_server_name_packet(), self.check_packet_sizeheader  )
        if self.get_packet_code(response) != 0x23:
            raise Exception("unexpected packet response")
        self.server_name = util.unpack_str( response, 36, 16)

        if len(self.lobby.char_data) == 0:
            self.is_new_char = True
            await self.create_char()
            await self.choose_login_char()
            return
        else:
            self.is_new_char = False

        self.char = self.himi.chars[ self.lobby.char_data[0].charID ]
        self.char.id = self.lobby.char_data[0].charID
        self.char.lobby_data = self.lobby.char_data[0]
        await self.view_conn.write_now( self.create_view_char_login_choice_packet(self.lobby.char_data[0]) )
        response = await self.data_conn.reader.read(5)
        if response[0] != 2:
            raise Exception("cannot choose this character")

        await self.login_char()

    async def login_char(self):
        #self.blowfish = self.init_blowfish()

        await self.data_conn.write_now( self.create_data_char_login_packet(encrypt=False) )
        response = await self.view_conn.reader.readexactly(72)
        self.zone_ip = util.unpack_ip( response, 0x38)
        self.zone_port = util.unpack_uint16(response, 0x3C)
        self.search_ip = util.unpack_ip( response, 0x40)
        self.search_port = util.unpack_uint16(response, 0x44)
        self.state.logged_in = True
        self.goals = [Goal("zonein")]