
from common import *
from .models import *

class HiveMind(object):
    def __init__(self):
        self.zk = kazoo.client.KazooClient(hosts=f'{config.server_ip}:2182')
        self.zk.start()
        self.zkh = ZKHelper(self.zk)

        self.db = mysql.connector.connect(host=config.server_ip, user ="root", passwd ="root", database='himi')
        self.xidb = mysql.connector.connect(host=config.server_ip, user ="root", passwd ="root", database='xidb')

        self.accounts = {}

        self.entities = collections.defaultdict(Entity)
        self.chars = collections.defaultdict(Char)
        #self.zonemaps = collections.defaultdict(ZoneMap)

        self.gear_optimizer = util.GearOptimize(self)

        self.town_zones = [z for z in range(230,242)]

        self.load_resources()
        self.load_zoneline_data()
        self.load_gear()

    def init_db(self):
        cur = self.db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS accounts (acct_id int(5) NOT NULL, username char(16) NOT NULL, password char(16) NOT NULL, PRIMARY KEY (acct_id) )")
        cur.close()

    def init_process_accounts(self, lo, hi):
        self.accounts_range = Object(lo=lo, hi=hi)
        self.accounts_current = lo
        cur = self.db.cursor()
        cur.execute("SELECT acct_id,username,password FROM accounts WHERE acct_id >= %s AND acct_id < %s", (lo, hi) )
        for row in cur:
            acct = Account()
            SQLHelper.read_row(acct, Account, row)
            self.accounts[acct.id] = acct
        cur.close()

    def get_next_account(self):
        if self.accounts_current >= self.accounts_range.hi:
            return None
        acct_id = self.accounts_current
        self.accounts_current += 1
        cur = self.db.cursor()
        if acct_id not in self.accounts:
            acct = Account()
            acct.generate(acct_id)
            cur.execute( *SQLHelper.insert(acct, Account) )
            self.db.commit()
        else:
            acct = self.accounts[acct_id]
        cur.close()
        return acct

    def load_resources(self):
        def fix_name(name):
            name = name.strip('\n')
            if len(name) > 16:
                return None
            if name.count('\'') == 1:
                splits = name.split('\'')
                name = splits[0].capitalize() + splits[1].capitalize()
            if name.count(' ') == 1:
                splits = name.split(' ')
                name = splits[0].capitalize() + splits[1].capitalize()
            return name

        with open( config.resource_folder / "char_names.txt", "r") as f:
            self.char_names_all = [fix_name(name) for name in f.readlines()]

        self.exp_hunt = {}
        with open( config.resource_folder / "exp_hunt.txt", "r") as f:
            for line in f.readlines():
                if line.startswith("r"):
                    continue
                data = line.split(",")
                if len(data) != 3:
                    raise Exception("bad line")
                self.exp_hunt[ int(data[0]) ] = Object(lo=int(data[1]), hi=int(data[2]))

    def load_zoneline_data(self):
        cursor = self.xidb.cursor()
        cursor.execute("SELECT zoneline,fromzone,tozone,tox,toy,toz FROM `zonelines`")
        zone_links = {}
        for zoneline in cursor.fetchall():
            zone_links[(zoneline[1], zoneline[2])] = {"id":zoneline[0], "loc":util.Point(zoneline[3], zoneline[4], zoneline[5])}
        self.zone_links = zone_links
        cursor.close()

    def load_gear(self):
        self.eq_infos = {}
        self.eq_mods = collections.defaultdict(list)
        self.skill_ranks = {}

        cursor = self.xidb.cursor()
        query = "SELECT itemId,name,level,jobs,slot FROM item_equipment"
        cursor.execute(query)
        for row in cursor:
            self.eq_infos[row[0]] = {"id":row[0], "name":row[1], "level":row[2], "jobs":row[3], "slot":row[4], "weapon":False}

        query = "SELECT itemId,modId,value from item_mods"
        cursor.execute(query)
        for row in cursor:
            if row[0] in self.eq_infos:
                eqinfo = self.eq_infos[row[0]]
                self.eq_mods[row[0]].append( (row[1],row[2]) )

        query = "SELECT itemId,skill,delay,dmg,name from item_weapon"
        cursor.execute(query)
        for row in cursor:
            if row[0] in self.eq_infos:
                eqinfo = self.eq_infos[row[0]]
                eqinfo["weapon"] = True
                eqinfo["skill"] = row[1]
                eqinfo["delay"] = row[2]
                eqinfo["dmg"] = row[3]
                if eqinfo["dmg"] == 0 or eqinfo["delay"] == 0:
                    continue
                eqinfo["DPS"] = 100 * eqinfo["dmg"] / eqinfo["delay"]

        query = "SELECT * FROM skill_ranks"
        cursor.execute(query)
        for row in cursor:
            for jid in range(1,23):
                self.skill_ranks[ (jid,row[0]) ] = row[jid+1]
        cursor.close()

    def cleanup(self):
        self.zk.stop()

    