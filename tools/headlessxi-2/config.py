
from common import *

source_dir = "../../"

login_port = 54231
data_port = 54230
view_port = 54001

def load_data():
    data = {}
    with open('gen/accounts.json', "r") as f:
        data["accounts"] = json.load(f)    
    return data

