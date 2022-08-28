
from common import *

class Account(SimpleObject):
    attrs = {
        "id":{"col":"acct_id"}, 
        "username":{}, 
        "password":{}
    }
    table = "accounts"
    primary_key = Object(attr='id', col="acct_id")

    def __init__(self):
        self.id = None
        self.username = None
        self.password = None

    def generate(self, acct_id):
        self.id = acct_id
        self.username = util.randomword( random.randint(6,12) )
        self.password = util.randomword( random.randint(6,12) )