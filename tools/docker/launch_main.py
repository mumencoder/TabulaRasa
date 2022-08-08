
import os, subprocess
import helpers

os.chdir( os.getenv('XI_BINARY_DIR') )

helpers.wait_for_db()
helpers.assign_zone_ips()

subprocess.run("nohup ./xi_connect &", shell=True)
subprocess.run("nohup ./xi_search &", shell=True)
subprocess.run(f"./xi_map", shell=True)