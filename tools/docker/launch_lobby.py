

import os, subprocess
import helpers

os.chdir( os.getenv('XI_BINARY_DIR') )

helpers.wait_for_db()
helpers.assign_zone_ips()

subprocess.run("./xi_connect &", shell=True)
subprocess.run("nohup ./xi_search &", shell=True)
