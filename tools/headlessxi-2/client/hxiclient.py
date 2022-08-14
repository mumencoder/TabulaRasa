
from common import *

import config
from packets import *
import util

from .packets_in import *
from .packets_out import *
from .tasks import *
from .models import *

class HXIClientState(object):
    pass

class HXIClient(ClientPacketsIn, ClientPacketsOut, ClientTasks):
    def __init__(self, account, server_host, client_ver=''):
        self.running = True
        self.account = account
        self.server_host = server_host
        self.connected = False
        self.starting_key = [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0xAD5DE056]
        self.send_key = bytearray(0)*20
        if client_ver == '':
            self.client_ver = self.get_client_ver()
        else:
            self.client_ver = "30220705_0" 

        self.created_chars = []
        self.is_new_char = None

        self.current_char = None

        self.char = model.Char()

        self.task_queue = collections.deque()
        self.processing_tasks = True

        self.in_packet_queue = collections.deque()
        self.packet_watchers = {}
        self.processing_packets = True

        self.state = HXIClientState()
        self.state.current = "logging in"

        self.init_packets_in()

        self.add_task( {"action":self.do_account_login} )

    async def update(self):
        if self.processing_packets is True:
            self.do_next_packet()
        if self.processing_tasks is True:
            await self.do_next_task()

    async def check_packet_sizeheader(self, stream):
        sizebytes = await stream.readexactly(4)
        size = util.unpack_uint32(sizebytes, 0)
        if size > 4096:
            raise Exception("bad view response size")
        response = await stream.readexactly(size - 4)
        if util.unpack_str(response, 0, 4) != 'IXFF':
            raise Exception("bad view response header", util.unpack_str(response, 0, 4))
        return sizebytes + response

    async def write_with_response(self, writer, reader, packet):
        await write_now(writer, packet)
        response = await self.check_packet_sizeheader( reader )
        return response

    def get_packet_code(self, packet):
        return util.unpack_uint32(packet, 8)

    def get_client_ver(self):
        with open(os.path.join(config.source_dir, 'settings/default/login.lua')) as f:
            settings_file = f.read()
            client_str = re.search(r'CLIENT_VER = "(.*?)"', settings_file)[1]
        return client_str

