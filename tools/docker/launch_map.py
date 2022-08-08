
import helpers
import subprocess, os

os.chdir( os.getenv('XI_BINARY_DIR') )

helpers.wait_for_db()

subprocess.run(f"./xi_map --ip {os.getenv('XI_NETWORK_MAP_HOST')} --port {os.getenv('XI_NETWORK_MAP_PORT')}", shell=True)