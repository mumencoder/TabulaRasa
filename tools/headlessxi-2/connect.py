
from common import *
from hxiclient import *

data = config.load_data()

account = random.choice( data["accounts"] )

print( account )

#account = {"name":"admin", "pass":"admin"} 

async def main():
    client = HXIClient(account, "192.168.36.103")
    while len(client.tasks) > 0:
        await asyncio.sleep(0.2)
        await client.update()

asyncio.run( main() )