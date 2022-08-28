
from common import *
from client import *

async def main(clients=None):
    all_updates = {}
    wait_times = {}

    def print_updates():
        if len(all_updates) != 0:
            print(f"players: {len(all_updates)} updates: {sum(all_updates.values())/len(all_updates)} waits: {sum(wait_times.values())/len(wait_times)}" )
            all_updates.clear()
            wait_times.clear()

    async def new_client(client_id, full_debug=False):
        account = himi.get_next_account()
        client = HXIClient(himi, client_id, account, config.server_ip, full_debug=full_debug)
        current_sec = int(time.time())
        updates, wait_time = 0, 0
        while client.running:
            ctime = time.time()
            if int(ctime) != current_sec:
                current_sec = int(ctime)
                all_updates[account.username] = updates
                wait_times[account.username] = wait_times
                updates, wait_time = 0, 0
            if updates > (ctime - int(ctime)) * 25:
                await asyncio.sleep(0.02)
                wait_time += 0.02
                continue
            await client.update()
            updates += 1

    himi = HiveMind()
    himi.init_db()
    himi.init_process_accounts(5, 245)

    tasks = []
    for i in range(5, 245):
        task = new_client(i+1)
        tasks.append( asyncio.create_task( task ) )
        try:
            for co in asyncio.as_completed(tasks, timeout=1.0):
                await co
        except asyncio.exceptions.TimeoutError:
            pass
        print_updates()
    while True:
        print_updates()
        try:
            for co in asyncio.as_completed(tasks, timeout=30.0):
                await co
        except asyncio.exceptions.TimeoutError:
            pass

def run_main():
    asyncio.run( main(clients=3) )

t = threading.Thread(target=run_main)
t.start()