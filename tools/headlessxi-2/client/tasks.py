
from common import *

import config
from packets import *
import util

class ClientTasks(object):
    def add_task(self, task):
        self.task_queue.append( task )

    async def do_next_task(self):
        if len(self.task_queue) > 0:
            self.current_task = self.task_queue[0]
            self.task_queue.popleft()
            await self.current_task

    async def do_account_login(self):
        (self.login_reader, self.login_writer) = await asyncio.open_connection(host=self.server_host, port=config.login_port)

        response = await request_and_wait( self.login_writer, self.login_reader, self.create_auth_login_packet( 0x10 ) )
        if response[0] == 1:
            self.account_id = util.unpack_uint16(response, 1)
            self.add_task( self.enter_lobby() )
        elif response[0] == 2:
            self.add_task( self.create_account() )
            return
        else: 
            raise Exception("unknown response code", response)

    async def create_account(self):
        (self.login_reader, self.login_writer) = await asyncio.open_connection(host=self.server_host, port=config.login_port)

        response = await request_and_wait(self.login_writer, self.login_reader, self.create_auth_login_packet( 0x20 ) )
        if response[0] == 3:
            self.add_task( self.do_account_login() )
        else:
            raise Exception("unknown response code", response)

    async def refresh_lobby(self):
        await write_now( self.view_writer, self.create_view_ready_packet() )
        data_response = await self.data_reader.readexactly(5)
        if data_response[0] != 1:
            raise Exception("data not ready")

        await write_now( self.data_writer, self.create_data_ready_packet() )
        data_response = await self.data_reader.readexactly(328)
        view_response = await self.check_packet_sizeheader( self.view_reader )

        char_data = []
        hasChars = True
        i = 0
        while hasChars:
            charListOffset = 32 + i * 140
            if charListOffset + 78 > len(view_response):
                hasChars = False
                continue
            char_entry = {}
            char_entry["contentID"] = util.unpack_uint32(view_response, charListOffset )
            if char_entry["contentID"] != 0:
                char_entry["charID"] = util.unpack_uint16(view_response, charListOffset + 4)
                char_entry["worldID"] = view_response[charListOffset+6]
                char_entry["charExtra"] = view_response[charListOffset+11]
                char_entry["name"] = util.unpack_str(view_response, charListOffset+12, 16)
                char_data.append( char_entry )
            i += 1

        return char_data

    async def enter_lobby(self):
        (self.data_reader, self.data_writer) = await asyncio.open_connection(host=self.server_host, port=config.data_port)
        (self.view_reader, self.view_writer) = await asyncio.open_connection(host=self.server_host, port=config.view_port)
        data_response = await self.data_reader.readexactly(5)
        if data_response[0] != 1:
            self.add_task( self.login_failed() )

        await write_now( self.data_writer, self.create_data_account_packet(self.account_id) )
        await write_now( self.view_writer, self.create_view_clientver_packet() )
        response = await self.view_reader.readexactly(40)
        self.expansion_bitmask = util.unpack_uint32(response, 32)
        self.feature_bitmask = util.unpack_uint32(response, 36)
        self.add_task( self.choose_login_char() )

    async def create_char(self):
        charname = random.choice( self.account["char_names"] )
        print("creating char", charname)
        response = await self.write_with_response( self.view_writer, self.view_reader, self.create_view_char_check_creation_packet(charname) )
        if self.get_packet_code(response) == 3:
            response = await self.write_with_response(self.view_writer, self.view_reader, self.create_view_char_creation_packet() )
            if self.get_packet_code(response) != 3:
                print("creation failed", response)
                await asyncio.sleep(10.0)
                self.add_task( self.create_char() )
                return
            print("character OK")
            self.created_chars.append( charname )
            self.add_task( self.choose_login_char() )
        else:
            print("character not available", response)
            await asyncio.sleep(10.0)
            self.add_task( self.create_char() )
            return

    async def choose_login_char(self):
        self.char_data = await self.refresh_lobby()
        response = await self.write_with_response(self.view_writer, self.view_reader, self.create_view_get_server_name_packet() )
        if self.get_packet_code(response) != 0x23:
            raise Exception("unexpected packet response", response[8], self.get_packet_code(response))
        self.server_name = util.unpack_str( response, 36, 16)

        if len(self.char_data) == 0:
            self.add_task( self.create_char() )
            return

        for char in self.char_data:
            if char["name"] not in self.account["char_names"]:
                raise Exception("unknown char")

        self.current_char = self.char_data[0]
        self.is_new_char = self.current_char["name"] in self.created_chars

        await write_now( self.view_writer, self.create_view_char_login_choice_packet(self.current_char) )
        response = await self.data_reader.read(5)
        if response[0] != 2:
            raise Exception("cannot choose this character")

        self.add_task( self.login_char() )

    async def login_char(self):
        #self.blowfish = self.init_blowfish()

        await write_now( self.data_writer, self.create_data_char_login_packet(encrypt=False) )
        response = await self.view_reader.readexactly(72)
        self.zone_ip = util.unpack_ip( response, 0x38)
        self.zone_port = util.unpack_uint16(response, 0x3C)
        self.search_ip = util.unpack_ip( response, 0x40)
        self.search_port = util.unpack_uint16(response, 0x44)
        self.add_task( self.enter_zone() )

    async def enter_zone(self):
        class MapProtocol(object):
            packet_code = 1

            def connection_made(proto, conn):
                proto.conn = conn
                print("connection made")

            def datagram_received(proto, data, addr):
                self.map_addr = addr
                for packet in MapPacket.parse_large_packet(data):
                    self.in_packet_queue.append( packet ) 

            def connection_lost(proto,conn):
                pass

        self.state.zoned_confirm = False
        if self.map_socket is not None and (self.map_addr[0] != self.zone_ip or self.map_addr[1] != self.zone_port):
            self.map_socket.conn.close()
            self.map_socket = None
        if self.map_socket is None:
            self.map_socket = MapProtocol()
            await asyncio.get_event_loop().create_datagram_endpoint( lambda: self.map_socket, remote_addr=(self.zone_ip, self.zone_port) )
        self.send_map_packet( self.Client.zone_login(self.current_char["charID"]) )

    async def request_zone(self, zoneline):
        self.send_map_packet( self.Client.request_zone(zoneline) )

    async def dezone_confirm(self):
        self.send_map_packet( self.Client.dezone_confirm() )

    def player_sync(self):
        self.send_map_packet( self.Client.player_sync(self) )
