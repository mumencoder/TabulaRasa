
from common import *
from client import *

data = config.load_data()

account = random.choice( data["accounts"] )

print( account )

#account = {"name":"admin", "pass":"admin"} 

async def main():
    client = HXIClient(account, "172.31.177.56")
    while client.running:
        await asyncio.sleep(0.2)
        await client.update()

asyncio.run( main() )