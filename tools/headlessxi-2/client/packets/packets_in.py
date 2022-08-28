
from common import *
from .packets import *

class ClientPacketsIn(object):
    async def check_packet_sizeheader(self, stream):
        sizebytes = await stream.readexactly(4)
        size = util.unpack_uint32(sizebytes, 0)
        if size > 4096:
            raise Exception("bad view response size")
        response = await stream.readexactly(size - 4)
        if util.unpack_str(response, 0, 4) != 'IXFF':
            raise Exception("bad view response header", util.unpack_str(response, 0, 4))
        return sizebytes + response

    def init_packets_in(self):
        self.add_packet_watcher("0x8", self.react_nothing) # zone_visited
        self.add_packet_watcher("0xa", self.react_zone_in) # zone_in
        self.add_packet_watcher("0xb", self.react_server_ip) # server_ip
        self.add_packet_watcher("0xd", self.react_char) # char
        self.add_packet_watcher("0xe", self.react_entity_update) # entity_update
        self.add_packet_watcher("0x1b", self.react_char_jobs) # char_jobs
        self.add_packet_watcher("0x1c", self.react_inventory_size) # inventory_size
        self.add_packet_watcher("0x1d", self.react_nothing) # inventory_finish
        self.add_packet_watcher("0x1f", self.react_nothing) # inventory_assign
        self.add_packet_watcher("0x20", self.react_inventory_item) # inventory_item
        self.add_packet_watcher("0x28", self.react_action) # action
        self.add_packet_watcher("0x29", self.react_basic_message) # message_basic
        self.add_packet_watcher("0x37", self.react_char_update) # char_update
        self.add_packet_watcher("0x41", self.react_downloading_data_end) # stop_downloading
        self.add_packet_watcher("0x4f", self.react_downloading_data_start) # downloading_data
        self.add_packet_watcher("0x50", self.react_char_equip) # char_equip
        self.add_packet_watcher("0x51", self.react_nothing) # char_appearance
        self.add_packet_watcher("0x55", self.react_nothing) # key_items
        self.add_packet_watcher("0x56", self.react_nothing) # quest_mission_log
        self.add_packet_watcher("0x58", self.react_lockon) # lock_on
        self.add_packet_watcher("0x61", self.react_char_stats) # char_stats
        self.add_packet_watcher("0x67", self.react_nothing) # char_sync
        self.add_packet_watcher("0x8c", self.react_nothing) # merit_points_categories
        self.add_packet_watcher("0xaa", self.react_nothing) # char_spells
        self.add_packet_watcher("0xac", self.react_nothing) # char_abilities
        self.add_packet_watcher("0xae", self.react_nothing) # char_mounts
        self.add_packet_watcher("0xb4", self.react_nothing) # menu_config
        self.add_packet_watcher("0xca", self.react_nothing) # bazaar_message
        self.add_packet_watcher("0xd2", self.react_nothing) # treasure_find_item
        self.add_packet_watcher("0xdf", self.react_char_health) # char_health
        self.add_packet_watcher("0x182", self.react_pathfind) # pathfind

    @staticmethod
    def parseXYZLocation(packet,offset):
        return {"x": util.unpack_float(packet, offset), "y": util.unpack_float(packet, offset+4), "z": util.unpack_float(packet, offset+8) }

    @staticmethod
    def parseRXYZLocation(packet, offset):
        ret = {"rot":packet[offset]}
        ret.update(ClientPacketsIn.parseXYZLocation(packet, offset+1))
        return ret

    @staticmethod
    def parseSpeed(packet, offset):
        return {"speed":packet[offset], "subspeed":packet[offset+1] }

    @staticmethod
    def parseStats(packet, offset):
        offset = 0
        stats = {}
        for stat in ["str", "dex", "vit", "agi", "int", "mnd", "chr"]:
            stats[stat] = packet[offset]
            stats[stat + "plus"] = packet[offset+1]
            offset += 2
        return stats

    # TODO: not relative
    def parseCharHealth(self, packet, offset):
        return {
            "hp":util.unpack_uint32(packet, offset+8), "mp":util.unpack_uint32(packet, offset+0x0C), "tp":util.unpack_uint32(packet, offset+0x10),
            "hpp":packet[offset+0x16], "mpp":packet[offset+0x17] 
        }

    def react_nothing(self, packet):
        pass

    def react_lockon(self, packet):
        char_id = util.unpack_uint32(packet, 0x04)
        if char_id != self.char.id:
            return
        entity_id = util.unpack_uint32( packet, 0x08 )
        if entity_id == 0:
            self.state.fite_entity = None
        else:
            self.state.fite_entity = entity_id

    def react_downloading_data_start(self, packet):
        self.state.is_downloading = True

    def react_downloading_data_end(self, packet):
        self.state.is_downloading = False

    def react_zone_in(self, packet):
        char_id = util.unpack_uint32(packet, 0x04)
        if char_id != self.char.id:
            raise Exception("unexpected char_id")

        self.char.targets = {}
        self.char.target_id = util.unpack_uint16(packet, 0x08)
        self.char.targets[ self.char.target_id ] = self.char
        self.char.updateLocation( **self.parseRXYZLocation(packet, 0x0B) )
        self.char.updateSpeed( **self.parseSpeed(packet, 0x1C) )
        self.char.updateHpp( packet[0x1E] )
        self.char.updateZone( util.unpack_uint16(packet, 0x30) )

        # TODO: moghouse
        if packet[0x80] != 2:
            raise Exception("moghouse not supported")

        self.char.updateMJob( packet[0xB4] )
        self.char.updateSJob( packet[0xB7] )
        self.char.updateStats( **self.parseStats(packet, 0xCC) )

        self.send_map_packet( self.zone_confirm() )
        self.send_map_packet( self.char_info_request() )
        self.send_map_packet( self.player_info_request() )
        self.add_timer("sync", action=self.task_player_sync, interval=0.4)
        self.state.zoned_confirm = True

    def react_server_ip(self, packet):
        zone_ip = util.unpack_ip( packet, 0x08 )
        zone_port = util.unpack_uint16(packet, 0x0C )
        self.zone_ip = zone_ip
        self.zone_port = zone_port

    def react_char(self, packet):
        self.char.target_id = util.unpack_uint16(packet, 8)

    def react_char_equip(self, packet):
        self.char.updateEquipWorn( packet[0x04], packet[0x05], packet[0x06] ) 

    def react_char_abilities(self, packet):
        pass

    def react_char_stats(self, packet):
        self.char.mlvl = packet[0x0D]

    def react_action(self, packet):
        actor_id = util.unpack_uint32(packet, 5)
        targets = packet[0x09]
        action = util.unpack_bits(packet, 82, 4)
        offset = 82 + 4 + 64
        if action == 1:
            target_id = util.unpack_bits(packet, offset, 32)
            offset += 32
            self.aggro_history.append( Object(name="attack", actor=actor_id, target=target_id) )
            #print( f"action: {actor_id} attacked {target_id}" )
        else:
            print( f"unknown action", action)

    def react_char_jobs(self, packet):
        self.char.mjob = packet[0x08]
        self.char.sjob = packet[0x0B]

        self.char.job_unlocked = set()
        unlocked = util.unpack_uint32(packet, 0x0C)
        for i in range(0,23):
            if unlocked & (1 << i) != 0:
                self.char.job_unlocked.add(i)

        offset = 0x0C + 4
        self.char.job_lvls = {i:packet[offset+i] for i in range(0, 24)}

        if self.char.mjob != 0:
            self.char.mlvl = self.char.job_lvls[self.char.mjob]
        if self.char.sjob != 0:
            self.char.slvl = self.char.job_lvls[self.char.sjob]

    def react_char_health(self, packet):
        char_id = util.unpack_uint32(packet, 4)
        if char_id == self.char.id:
            self.char.updateHealth( **self.parseCharHealth(packet, 0) )
        else:
            self.getChar( char_id ).updateHealth( **self.parseCharHealth(packet, 0) )

    def react_inventory_item(self, packet):
        loc = (packet[0x0E], packet[0x0F])
        item = {"id": util.unpack_uint16(packet, 0x0C), "quantity": util.unpack_uint32(packet, 0x04) }
        self.char.updateInventory( loc, item )

    def react_basic_message(self, packet):
        sender_id = util.unpack_uint32(packet, 0x04)
        target_id = util.unpack_uint32(packet, 0x08)

        sender_targid = util.unpack_uint16(packet, 0x14)
        target_targid = util.unpack_uint16(packet, 0x16)

        param = util.unpack_uint32(packet, 0x0C)
        value = util.unpack_uint32(packet, 0x10)
        msgID = util.unpack_uint16(packet, 0x18)

        if msgID == 4: # out of range
            self.state.out_of_range = True
        elif msgID == 5: # unable to see
            self.state.unable_to_see = True
        elif msgID == 6: # sender_id defeats the target_id
            entity = self.himi.entities[ target_id ]
            entity.alive = False
        elif msgID == 12: # Cannot attack. Your target is already claimed.
            entity = self.himi.entities[ target_id ]
            self.claimed_targets.append( entity.id )
        elif msgID == 36: # you lose sight
            self.state.lost_sight = True
        elif msgID == 38: # skill up
            pass
        elif msgID == 53: # skill level up
            pass
        elif msgID == 78: # too far away
            self.state.msg_too_far = True
        elif msgID == 94: # you must wait longer to perform that action
            self.state.wait_longer = True
        elif msgID == 97: # defeated
            self.state.defeated = True
        elif msgID >= 170 or msgID <= 178:
            entity = self.himi.entities[ target_id ]
            entity.level = param
        elif msgID == 446: # you cannot attack that target
            self.state.attackable = False
        else:
            self.log(msg=f"MSG {sender_id}->{target_id} sender_target:{sender_targid} target_target:{target_targid} {param} {value} {msgID}")

    class UpdateType(object):
        POS      = 0x01
        STATUS   = 0x02
        HP       = 0x04
        COMBAT   = 0x07
        NAME     = 0x08
        LOOK     = 0x10
        ALL_MOB  = 0x0F
        ALL_CHAR = 0x1F
        DESPAWN  = 0x20

    def react_char_update(self, packet):
        self.char.hpp = packet[0x2A]
        self.char.speed = packet[0x2C]
        self.char.animation = packet[0x30]

    def react_entity_update(self, packet):
        entity_id = util.unpack_uint32(packet, 4)
        update_mask = packet[0x0A]

        entity = self.himi.entities[entity_id]
        entity.id = entity_id
        entity.zone = self.char.zone
        entity.target_id = util.unpack_uint16(packet, 0x08)
        self.char.targets[ entity.target_id ] = entity

        if update_mask & ClientPacketsIn.UpdateType.NAME != 0:
            entity.name = util.unpack_str(packet, 0x34, 16)
        if update_mask & ClientPacketsIn.UpdateType.HP != 0:
            entity.updateHPP( packet[0x1E] )
        if update_mask & ClientPacketsIn.UpdateType.POS != 0:
            entity.loc = util.Point.from_dict( self.parseXYZLocation(packet, 0x0C) )

        self.recent_entities.append( entity.id )

    def react_inventory_size(self, packet):
        self.char.updateInventorySize( "inv", packet[0x24] )
        self.char.updateInventorySize( "satchel", packet[0x2E] )

    def react_pathfind(self, packet):
        pts = util.unpack_uint16(packet, 0x04)
        self.state.pathfind_points = collections.deque()
        offset = 0x06
        for i in range(0,pts):
            loc = self.parseXYZLocation(packet, offset)
            destination = util.Point.from_dict(loc)
            if destination.x == 0.0 or destination.y == 0.0 or destination.z == 0.0:
                # TODO: this is potentially blocking behavior
                continue
            if util.Point.dist( self.char.get_point(), destination) > 3:
                self.state.pathfind_points.append( destination )
            offset += 12
