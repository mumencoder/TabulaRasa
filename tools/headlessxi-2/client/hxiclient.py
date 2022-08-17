
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

class Goal(object):
    def __init__(self, name):
        self.created = time.time()
        self.name = name

class MoveGoal(Goal):
    def __init__(self, name, final_destination):
        super().__init__(name)
        self.final_destination = final_destination
        self.move_destination = None
        self.sent_packet = False
        self.pathfind_failed = False

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

        self.waypoints = []

        self.created_chars = []
        self.is_new_char = None

        self.current_char = None

        self.char = model.Char()
        self.other_chars = {}
        self.entities = {}

        self.timers = {}
        self.processing_timers = True

        self.task_queue = collections.deque()
        self.processing_tasks = True

        self.goals = [Goal("login")]
        self.last_goal = None
        self.processing_goals = True

        self.in_packet_queue = collections.deque()
        self.packet_watchers = {}
        self.processing_packets = True

        self.state = HXIClientState()
        self.state.is_downloading = False
        self.state.zoned_confirm = False
        self.state.last_loc_update = time.time()

        self.map_socket = None
        self.map_addr = None
        self.init_packets_in()

        self.add_task( self.do_account_login() )

    async def update(self):
        if self.processing_packets is True:
            self.do_next_packet()
        if self.processing_tasks is True:
            await self.do_next_task()
        if self.processing_timers is True:
            self.process_timers()
        if self.processing_goals is True:
            self.process_goals()

    async def check_packet_sizeheader(self, stream):
        sizebytes = await stream.readexactly(4)
        size = util.unpack_uint32(sizebytes, 0)
        if size > 4096:
            raise Exception("bad view response size")
        response = await stream.readexactly(size - 4)
        if util.unpack_str(response, 0, 4) != 'IXFF':
            raise Exception("bad view response header", util.unpack_str(response, 0, 4))
        return sizebytes + response

    def add_timer(self, name, action=None, interval=None, do_now=False):
        timer = {}
        timer["name"] = name
        timer["interval"] = interval
        timer["action"] = action
        timer["last_tick"] = 0 if do_now else time.time()

        self.timers[name] = timer

    def direction(self, p1, p2):
        return self.norm( self.sub(p1, p2) )

    def smul(self, s, p):
        return Point( s*p.x, s*p.y, s*p.z )

    def add(self, p1, p2):
        return Point( p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

    def sub(self, p1, p2):
        return Point( p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)

    def nav_dist(self, p1, p2):
        if abs(p1.y - p2.y) < 3:
            return math.sqrt( (p1.x-p2.x)**2 + (p1.z-p2.z)**2 )
        else:
            return self.dist(p1, p2)

    def dist(self, p1, p2):
        return math.sqrt( (p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2 )

    def norm(self, p):
        N = self.dist(p, Point(0.0, 0.0, 0.0))
        return Point( p.x / N, p.y / N, p.z / N)

    def process_timers(self):
        for key, timer in self.timers.items():
            try:
                if timer["last_tick"] + timer["interval"] < time.time():
                    timer["action"]()
                    timer["last_tick"] = time.time()
            except:
                print( "timer error: ", timer["name"] )
                print( traceback.print_exc() )

    def process_goals(self):
        top_goal = self.goals[-1]
        if self.last_goal is not None:
            if self.goals[-1].name != self.last_goal.name:
                print("goal:", self.goals[-1].name)
        self.last_goal = self.goals[-1]

        if self.state.is_downloading:
            pass
        elif top_goal.name == "fite":
            if self.char.zone in self.server.town_zones:
                self.goals.append( Goal("leave_town") )
                return
        elif top_goal.name == "leave_town":
            if self.char.zone not in self.server.town_zones:
                self.goals.pop()
                return
            for zone_link, zoneline in self.server.zone_links.items():
                if zone_link[0] not in self.server.town_zones and zone_link[1] == self.char.zone:
                    if self.nav_dist( self.char.get_point(), zoneline["loc"]) < 5:
                        self.goals.append( Goal("idle") )
                        self.state.zoned_confirm = False
                        zone_link = (zone_link[1],zone_link[0])
                        self.add_task( self.request_zone( self.server.zone_links[zone_link]["id"] ) )
                    else:
                        self.goals.append( MoveGoal("move.wait_for_directions", zoneline["loc"]) )
        elif top_goal.name == "idle":
            if self.state.zoned_confirm:
                self.goals[-1] = Goal("fite") # kitty only knows fite
        elif top_goal.name == "login":
            if self.state.zoned_confirm:
                self.goals[-1] = Goal("idle")
        elif top_goal.name == "move.random":
            self.goals[-1] = MoveGoal("move.wait_for_directions", self.get_random_destination())
        elif top_goal.name == "move.wait_for_directions":
            if top_goal.pathfind_failed:
                self.goals.pop()
            elif self.nav_dist( self.char.get_point(), top_goal.final_destination ) < 2:
                self.goals.pop()
            elif top_goal.move_destination is not None:
                self.goals.append( Goal("move.moving") )
            elif top_goal.sent_packet is False:
                self.send_map_packet( self.Client.path_request(top_goal.final_destination) )
                top_goal.sent_packet = time.time()
            elif top_goal.sent_packet + 10 < time.time():
                top_goal.sent_packet = False
        elif top_goal.name == "move.moving":
            if self.nav_dist( self.char.get_point(), self.goals[-2].move_destination ) < 2:
                self.goals[-2].move_destination = None
                self.goals.pop()
            else:
                max_dist = self.dist( self.char.get_point(), self.goals[-2].move_destination )
                elapsed = time.time() - self.char.state.last_loc_update
                distance_travelled = elapsed * self.char.speed * 0.10

                n = self.direction( self.goals[-2].move_destination, self.char.get_point() ) 
                new_loc = self.add( self.char.get_point(), self.smul( min(max_dist, distance_travelled), n ) )
                print(new_loc.x, new_loc.y, new_loc.z)
                self.char.x = new_loc.x
                self.char.y = new_loc.y
                self.char.z = new_loc.z
                self.char.state.last_loc_update = time.time()

    def get_random_destination(self):
        return (self.char.x + random.randint(-10,10), self.char.y, self.char.z + random.randint(-10,10) )

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

    def get_char(self, cid):
        if cid not in self.other_chars:
            self.other_chars[cid] = model.Char()
        return self.other_chars[cid]
