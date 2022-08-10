
from common import *

import util

num_accts = 200
accts = []

def fix_char_name(name):
    name = name.strip('\n')
    if len(name) > 16:
        return None
    if name.count('\'') == 1:
        splits = name.split('\'')
        return splits[0] + splits[1]
    elif name.count(' ') == 1:
        splits = name.split(' ')
        return splits[0] + splits[1]
    else:
        return None

with open("char_names.txt", "r") as f:
    char_names = f.readlines()

for i in range(num_accts):
    acct = {}
    acct_len = random.randint(6,16)
    passwd_len = random.randint(6,16)
    acct["name"] = util.randomword( acct_len )
    acct["pass"] = util.randomword( passwd_len )
    acct["char_names"] = []
    for j in range(0, 3):
        acct["char_names"].append( fix_char_name( random.choice( char_names ) ) )
    accts.append( acct )

with open("gen/accounts.json", "w") as f:
    json.dump(accts, f)