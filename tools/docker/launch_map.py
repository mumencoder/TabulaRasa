
import helpers
import subprocess, os, time

os.chdir( os.getenv('XI_BINARY_DIR') )

helpers.wait_for_db()

map_ports = os.getenv('XI_NETWORK_MAP_PORTS').split(',')

for port in map_ports:
    subprocess.run(f"./xi_map --ip {os.getenv('XI_NETWORK_MAP_HOST')} --port {port} &", shell=True)

while True:
    time.sleep(1.0)