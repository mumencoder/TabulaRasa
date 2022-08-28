
from common import *

server_ip = "172.31.177.56"
source_dir = "../../"

login_ip = server_ip
login_port = 54231
data_ip = server_ip
data_port = 54230
view_ip = server_ip
view_port = 54001

script_folder = pathlib.Path( os.path.dirname(__file__) )
data_folder = pathlib.Path('/media/dream/headlessxi-2')
resource_folder = script_folder / 'resources'