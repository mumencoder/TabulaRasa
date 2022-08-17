
from common import *
from client import *

ip = "172.31.177.56"
class Server(object):
    def load_server_data(self):
        db = mysql.connector.connect(host=ip, user ="root", passwd ="root", database='xidb')
        cursor = db.cursor()
        cursor.execute("SELECT zoneline,fromzone,tozone,tox,toy,toz FROM `zonelines`")
        zone_links = {}
        for zoneline in cursor.fetchall():
            zone_links[(zoneline[1], zoneline[2])] = {"id":zoneline[0], "loc":Point(zoneline[3], zoneline[4], zoneline[5])}
        self.zone_links = zone_links
        self.town_zones = [238,239,240,241]

async def main():
    data = config.load_data()

    account = random.choice( data["accounts"] )
    print( account )

    server = Server()
    server.load_server_data()

    client = HXIClient(account, ip)
    client.server = server
    while client.running:
        await asyncio.sleep(0.1)
        await client.update()

asyncio.run( main() )