
from common import *

class Goal(object):
    def __init__(self, name):
        self.created = time.time()
        self.name = name

class MoveGoal(Goal):
    def __init__(self, name):
        super().__init__(name)
        self.move_destination = None
        self.sent_packet = False

class RestGoal(Goal):
    def __init__(self):
        super().__init__("resting")
        self.sent_packet = False

class CheckGoal(Goal):
    def __init__(self, entity):
        super().__init__("check.entity")
        self.entity = entity

class ZoningGoal(Goal):
    def __init__(self, name, zone):
        super().__init__(name)
        self.zone = zone
        self.sent_packet = False

class KnownMoveGoal(MoveGoal):
    def __init__(self, name, loc):
        super().__init__(name)
        self.final_destination = loc

class FiteGoal(Goal):
    def __init__(self, name, entity):
        super().__init__(name)
        self.name = name
        self.entity = entity
        self.engaging = "start"

class ClientGoals(object):
    def scan_goals(self, names):
        for goal in self.goals:
            if goal.name in names:
                return True
        return False

    async def process_goals(self):
        if len(self.goals) == 0:
            self.goals = [Goal("idle")]

        top_goal = self.goals[-1]
        if self.last_goal_name is not None:
            if self.goals[-1].name != self.last_goal_name:
                self.log(msg="goal change", goal=self.goals[-1], name=self.goals[-1].name)
        self.last_goal_name = self.goals[-1].name
           
        if self.state.logged_in is False:
            self.init_lobby()
            await self.auth_try_login()
            return

        if self.state.is_downloading:
            return

        if top_goal.name == "zonein":
            if self.state.zoned_confirm is None:
                self.state.zoned_confirm = False
                self.add_task( self.enter_zone( ) )
            elif self.state.zoned_confirm is True:
                self.state.zoned_confirm = None
                self.goals = [Goal("idle")]
            return

        if self.char.hpp == 0 and not self.state.ded_handled:
            self.state.fite_entity = None
            self.state.ded_handled = True
            self.reset_aggro()
            only_goal = Goal("move.homepoint")
            only_goal.wait = time.time() + 5
            self.goals = [only_goal]
            return
        elif self.char.hpp != 0 and self.state.ded_handled:
            self.state.ded_handled = False
        elif not self.state.gear_checked:
            desired_gear = self.gear_check()
            self.equip_gear(desired_gear)
            self.state.gear_checked = True
        elif len(self.aggro_entities) > 0 and self.attack_ready():
            self.goals = [FiteGoal("fite.attack", random.choice( self.aggro_entities ) )]
            return
        elif self.char.hpp is not None and self.char.hpp > 0 and self.char.hpp < 80 and not self.scan_goals(["fite.wait_engage", 'fite.attack', 'fite.engaged', 'resting']):
            self.goals = [RestGoal()]
            return
        elif self.state.wanna_fite is not None and self.attack_ready():
            self.goals = [FiteGoal("fite.attack", self.state.wanna_fite)]
            return
        elif top_goal.name in ["fite.wait_engage", 'fite.attack', 'fite.engaged']:
            if self.state.msg_too_far == True:
                self.state.msg_too_far = None
                self.goals.append( KnownMoveGoal("move.request.path_to", self.get_attack_approach(top_goal.entity)))
                top_goal.name = 'fite.attack'
                return
            elif self.state.out_of_range == True:
                self.state.out_of_range = False
                self.goals.append( KnownMoveGoal("move.request.path_to", self.get_attack_approach(top_goal.entity)))
                return
            elif self.state.unable_to_see == True:
                self.state.unable_to_see = None
                self.goals.append( KnownMoveGoal("move.request.path_to", self.get_attack_approach(top_goal.entity)))
                return

        if top_goal.name == "idle":
            self.goals[-1] = Goal("fite.search") # kitty only knows fite
        elif top_goal.name == "resting":
            if self.char.animation != 33 and self.char.hpp < 100 and not top_goal.sent_packet:
                if len(self.aggro_entities) > 0:
                    #print("too dangerous to rest")
                    return
                self.send_map_packet( self.command_heal() )
                top_goal.sent_packet = True
            elif self.char.animation == 33 and self.char.hpp == 100:
                self.send_map_packet( self.command_heal() )
                self.char.state.last_loc_update = time.time()
                self.goals.pop()
            elif self.char.animation == 33:
                if len(self.aggro_entities) > 0:
                    self.send_map_packet( self.command_heal() )
                    self.char.state.last_loc_update = time.time()
                    self.goals.pop()
                    #print("aborting rest")
                    return
                top_goal.sent_packet = False
        elif top_goal.name == "fite.search":
            if self.char.zone in self.himi.town_zones:
                self.goals.append( Goal("move.leave_town") )
            elif self.state.wanna_fite is None:
                self.goals.append( MoveGoal("move.request.random_path") )
        elif top_goal.name == "fite.attack":
            if not self.can_engage_entity( top_goal.entity ):
                self.state.fite_entity = None
                self.state.wanna_fite = None
                self.goals.pop()
                return
            else:
                self.send_map_packet( self.player_action_engage( top_goal.entity ) )
                top_goal.sent_packet = time.time()
                top_goal.name = "fite.wait_engage"
        elif top_goal.name == "fite.wait_engage":
            self.char.rot = util.Point.lookat( self.char.get_point(), top_goal.entity.loc )
            if not self.can_engage_entity( top_goal.entity ):
                self.state.fite_entity = None
                self.state.wanna_fite = None
                self.goals.pop()
            elif self.state.fite_entity is not None:
                top_goal.entity.attackable = True
                top_goal.name = "fite.engaged"
            elif top_goal.sent_packet + 3 < time.time():
                top_goal.name = "fite.attack"
        elif top_goal.name == "fite.engaged":
            self.char.rot = util.Point.lookat( self.char.get_point(), top_goal.entity.loc )
            if self.state.fite_entity is None:
                top_goal.name = "fite.attack"
            elif not self.can_engage_entity( top_goal.entity ):
                self.state.fite_entity = None
                self.state.wanna_fite = None
                self.goals.pop()
            elif self.state.lost_sight is True:
                self.state.lost_sight = None
                self.goals = [Goal("idle")]
            elif top_goal.entity.alive is False:
                self.goals = [Goal("idle")]
        elif top_goal.name == "move.homepoint":
            if top_goal.wait < time.time():
                self.send_map_packet( self.player_action_homepoint() )
                self.remove_timer("sync")
                self.add_task( self.task_dezone_confirm() )
                self.goals = [ Goal('zonein') ]
        elif top_goal.name == "move.zoning":
            if top_goal.sent_packet is False:
                top_goal.sent_packet = True
                self.send_map_packet( self.request_zone(top_goal.zone) )
            elif self.zone_ip is not None:
                self.remove_timer("sync")
                self.add_task( self.task_dezone_confirm() )
                self.goals[-1] = Goal("zonein")
        elif top_goal.name == "move.leave_town":
            if self.char.zone not in self.himi.town_zones:
                self.goals.pop()
                return
            for zone_link, zoneline in self.himi.zone_links.items():
                if zone_link[0] not in self.himi.town_zones and zone_link[1] == self.char.zone:
                    if util.Point.nav_dist( self.char.get_point(), zoneline["loc"]) < 5:
                        zone_link = (zone_link[1],zone_link[0])
                        self.goals.append( ZoningGoal("move.zoning", self.himi.zone_links[zone_link]["id"]) )
                        self.zone_ip = None
                        self.zone_port = None
                    else:
                        self.goals.append( KnownMoveGoal("move.request.path_to", zoneline["loc"]) )
        elif top_goal.name == "move.request.random_path":
            if self.state.pathfind_points is not None and len(self.state.pathfind_points) == 0:
                self.state.pathfind_points = None
                self.goals.pop()
            elif top_goal.sent_packet is False:
                self.state.pathfind_points = None
                self.send_map_packet( self.random_path_request(self.char.get_point(), 40, 0) )
                top_goal.sent_packet = time.time()
                self.goals.append( Goal("move.wait_path_request") )
            elif top_goal.sent_packet + 10 < time.time():
                top_goal.sent_packet = False
        elif top_goal.name == "move.request.path_to":
            if util.Point.nav_dist( self.char.get_point(), top_goal.final_destination ) < 2:
                self.goals.pop()
            elif self.state.pathfind_failed is True:
                self.state.pathfind_failed = None
                self.goals.pop()
            elif top_goal.sent_packet is False:
                self.state.pathfind_points = None
                self.send_map_packet( self.to_point_path_request(top_goal.final_destination) )
                top_goal.sent_packet = time.time()
                self.goals.append( Goal("move.wait_path_request") )
            elif top_goal.sent_packet + 10 < time.time():
                top_goal.sent_packet = False
        elif top_goal.name == "move.wait_path_request":
            if self.state.pathfind_points is not None:
                if len(self.state.pathfind_points) == 0:
                    self.state.pathfind_failed = True
                    self.goals.pop()
                self.char.state.last_loc_update = time.time()
                top_goal.name = "move.moving"
        elif top_goal.name == "move.moving":
            if len(self.state.pathfind_points) == 0:
                self.goals.pop()
                return
            move_to_p = self.state.pathfind_points[0]
            self.char.rot = util.Point.lookat( self.char.get_point(), move_to_p )
            if util.Point.nav_dist( self.char.get_point(), move_to_p ) < 2:
                self.log(msg="moved", point=str(move_to_p) )
                self.state.pathfind_points.popleft()
            else:
                max_dist = util.Point.dist( self.char.get_point(), move_to_p )
                elapsed = time.time() - self.char.state.last_loc_update
                distance_travelled = elapsed * self.char.speed * 0.10

                n = util.Point.direction( move_to_p, self.char.get_point() ) 
                new_loc = util.Point.add( self.char.get_point(), util.Point.smul( min(max_dist, distance_travelled), n ) )
                self.char.x = new_loc.x
                self.char.y = new_loc.y
                self.char.z = new_loc.z

                self.char.state.last_loc_update = time.time()
        else:
            raise Exception("unknown goal state")