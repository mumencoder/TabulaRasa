
from common import *
from .packets import *

class ClientTasks(object):
    async def enter_zone(self):
        class MapProtocol(object):
            def connection_made(proto, conn):
                proto.conn = conn

            def datagram_received(proto, data, addr):
                self.map_addr = addr
                for packet in MapPacket.parse_large_packet(data):
                    self.in_packet_queue.append( packet ) 

            def connection_lost(proto,conn):
                pass

            def error_received(proto,exc):
                print("map socket error", exc)

        self.state.zoned_confirm = False
        if self.map_socket is not None and (self.map_addr[0] != self.zone_ip or self.map_addr[1] != self.zone_port):
            self.map_socket.conn.close()
            self.map_socket = None
        if self.map_socket is None:
            self.map_socket = MapProtocol()
            await asyncio.get_event_loop().create_datagram_endpoint( lambda: self.map_socket, 
                remote_addr=(self.zone_ip, self.zone_port), local_addr=(self.local_host, random.randint(35000,40000)) )
        self.send_map_packet( self.zone_login(self.char.id) )

    async def request_zone(self, zoneline):
        self.send_map_packet( self.request_zone(zoneline) )

    async def task_dezone_confirm(self):
        self.send_map_packet( self.dezone_confirm() )

    def task_player_sync(self):
        self.send_map_packet( self.player_sync(self) )
