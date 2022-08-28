
from common import *

from .packets import *
from .goals import *
from .tasks import *
from .models import *

class HXIClientState(object):
    attrs = {
        "is_downloading":{},
        "last_loc_update":{},
        "pathfind_points":{},
        "pathfind_failed":{},
        "zoned_confirm":{},
        "attackable":{},
        "out_of_range":{},
        "msg_too_far":{},
        "unable_to_see":{},
        "fite_entity":{},
        "wanna_fite":{},
        "ded_handled":{},
        "logged_in":{"default":False},
        "wait_longer":{},
        "lost_sight":{},
        "gear_checked":{"default":False}
    }

    def __init__(self):
        for attr, info in self.attrs.items():
            if "default" in info:
                setattr(self, attr, info["default"])
            else:
                setattr(self, attr, None)

class HXIClient(ClientPacketsIn, ClientPacketsOut, ClientTasks, ClientGoals, ClientLobby):
    def __init__(self, himi, client_id, account, server_host, client_ver='', full_debug=False):
        self.himi = himi
        self.account = account
        self.server_host = server_host
        if client_ver == '':
            self.client_ver = self.get_client_ver()
        else:
            self.client_ver = "30220705_0" 
        self.full_debug = full_debug

        self.running = True

        self.char = None

        self.processing_timers = True
        self.timers = {}

        self.processing_tasks = True
        self.task_queue = collections.deque()

        self.processing_goals = True
        self.goals = [Goal("idle")]
        self.last_goal_name = None

        self.processing_in_packets = True
        self.in_packet_queue = collections.deque()
        self.packet_watchers = {}
        self.init_packets_in()

        self.processing_out_packets = True
        self.out_packet_queue = collections.deque()

        self.state = HXIClientState()

        self.login_conn = None
        self.data_conn = None
        self.view_conn = None
        self.map_socket = None
        self.map_addr = None

        self.aggro_history = util.Cache()
        self.aggro_entities = []
        self.recent_entities = util.SetCache()
        self.claimed_targets = util.SetCache()
        
        self.local_host = f"172.31.176.{client_id}"

        # TODO: add a gear check/equip timer
        self.add_timer("gearcheck", action=self.clear_gear_check, interval=60*20)
        self.add_timer("cache_expire", action=self.cache_expire, interval=60)
        self.add_timer("find_checkable", action=self.find_check_target, interval=15)
        self.add_timer("aggro_check", action=self.check_aggro, interval=2)
        self.add_timer("find_fiteable", action=self.find_fite_target, interval=1)
        
    def log(self, **kwargs):
        if self.full_debug is True:
            print(kwargs)

    async def update(self):
        if self.processing_in_packets is True:
            self.process_in_packets()
        if self.processing_tasks is True:
            await self.process_tasks()
        if self.processing_timers is True:
            self.process_timers()
        if self.processing_goals is True:
            await self.process_goals()
        if self.processing_out_packets is True:
            self.process_out_packets()

    def add_task(self, task):
        if self.full_debug is True:
            print(task)
        self.task_queue.append( task )

    async def process_tasks(self):
        while len(self.task_queue) > 0:
            self.current_task = self.task_queue[0]
            self.task_queue.popleft()
            await self.current_task

    def add_timer(self, name, action=None, interval=None, do_now=False):
        timer = Object(name=name, interval=interval, action=action, last_tick=(0 if do_now else time.time()) )
        self.timers[name] = timer

    def remove_timer(self, name):
        del self.timers[name]

    def process_timers(self):
        for key, timer in dict(self.timers).items():
            try:
                if timer.last_tick + timer.interval < time.time():
                    timer.action()
                    timer.last_tick = time.time()
            except:
                self.log(msg="timer error", timer=timer, traceback=traceback.print_exc() )

    def process_in_packets(self):
        while len(self.in_packet_queue) > 0:
            self.current_packet = self.in_packet_queue[0]
            self.in_packet_queue.popleft()
            self.process_in_packet(self.current_packet)

    def process_out_packets(self):
        while len(self.out_packet_queue) > 0:
            conn, data = self.out_packet_queue[0]
            self.out_packet_queue.popleft()
            self.process_out_packet(conn, data)

    def add_packet_watcher(self, ty, action):
        if ty not in self.packet_watchers:
            self.packet_watchers[ty] = [action]
        else:
            self.packet_watchers[ty].append( action )

    def process_in_packet(self, packet):
        if packet["type"] not in self.packet_watchers:
            self.log(msg=f"unprocessed packet", packet=packet)
        else:
            for watcher in self.packet_watchers[packet["type"]]:
                watcher(packet["data"])

    def process_out_packet(self, conn, data):
        conn.sendto( data )

    def find_check_target(self):
        for entity_id in self.recent_entities.items():
            entity = self.himi.entities[entity_id]
            if not self.entity_nearby(entity):
                continue
            if entity.level is None:
                self.send_map_packet( self.command_check(entity) )
        return None

    def entity_nearby(self, entity):
        if entity.loc is not None and util.Point.nav_dist(self.char.get_point(), entity.loc) > 100:
            return False
        return True

    def entity_huntable(self, entity):
        hunt_lvls = self.himi.exp_hunt[ self.char.mlvl ]
        if entity.level is None:
            return False
        return hunt_lvls.lo <= entity.level and entity.level <= hunt_lvls.hi

    def can_engage_entity(self, entity):
        if entity.zone != self.char.zone:
            return False
        if entity.target_id is None:
            return False
        if entity.hpp is not None and not entity.hpp > 0:
            return False
        if entity.alive is False:
            return False
        if entity.id in self.claimed_targets:
            return False
        if entity.attackable is False:
            return False
        return True

    def want_engage_entity(self, entity):
        if not self.can_engage_entity(entity):
            return False
        if not self.entity_nearby(entity):
            return False
        if not self.entity_huntable(entity):
            return False
        if entity.attackable is None:
            return True
        if entity.attackable is True:
            return True
        return False

    def find_fite_target(self):
        if self.state.wanna_fite is not None:
            if not self.want_engage_entity(self.state.wanna_fite):
                self.state.wanna_fite = None
        for entity_id in self.recent_entities.items():
            entity = self.himi.entities[entity_id]
            if self.want_engage_entity(entity):
                self.state.wanna_fite = entity
                return

    def get_attack_approach(self, entity):
        if entity.loc is None:
            return self.char.get_point()
        n = util.Point.direction( entity.loc, self.char.get_point() ) 
        approach = util.Point.add( entity.loc, util.Point.neg( util.Point.smul(0.3,n) ) )
        return approach

    def gear_check(self):
        desired_equip = self.himi.gear_optimizer.optimize( [i["id"] for i in self.char.inventory.values()], self.char.mlvl, self.char.mjob )
        return desired_equip

    def equip_gear(self, desired_equip):
        for slot_id, equipment in desired_equip.items():
            equipped = self.char.equipped_item(slot_id)
            loc = self.char.find_item( equipment["id"] )
            if equipped is None:
                self.send_map_packet( self.gear_change(loc, slot_id) )
            elif equipped["id"] == equipment["id"]:
                continue
            else:
                self.send_map_packet( self.gear_change(loc, slot_id) )

    def cache_expire(self):
        self.claimed_targets.expire(t=time.time()-5*60)
        self.recent_entities.trim(128)
        self.aggro_history.trim(32)
        self.aggro_history.expire(t=time.time()-30)

    def clear_gear_check(self):
        self.state.gear_checked = False

    def reset_aggro(self):
        self.aggro_entities = []
        self.aggro_history.clear()

    def attack_ready(self):
        if self.char.hpp == 0:
            return False
        if self.scan_goals( ["fite.wait_engage", 'fite.attack', 'fite.engaged', 'resting', 'move.homepoint'] ):
            return False
        return True

    def check_aggro(self):
        self.aggro_entities = []
        for act in self.aggro_history.items():
            if act.name == "attack" and act.target == self.char.id:
                entity = self.himi.entities[act.actor]
                if self.can_engage_entity(entity):
                    self.aggro_entities.append( entity )