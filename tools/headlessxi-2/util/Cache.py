
from common import *

class Cache(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.q = collections.deque()

    def append(self, item, t=None):
        if t is None:
            t = time.time() 
        self.q.append( (t, item) )

    def trim(self, n):
        if n < len(self.q):
            for i in range(0, len(self.q)-n):
                self.q.popleft()

    def expire(self, t=None):
        new_q = collections.deque()
        for e in self.q:
            if e[0] >= t:
                new_q.append(e)
        self.q = new_q

    def items(self):
        for e in self.q:
            yield e[1]

class SetCache(Cache):
    def __init__(self):
        self.clear()

    def clear(self):
        self.q = collections.deque()
        self.s = set()
    
    def append(self, item, t=None):
        if t is None:
            t = time.time() 
        self.q.append( (t, item) )
        self.s.add( item )

    def trim(self, n):
        if n < len(self.q):
            for i in range(0, len(self.q)-n):
                e = self.q.popleft()
                if e[1] in self.s:
                    self.s.remove( e[1] )

    def expire(self, t=None):
        new_q = collections.deque()
        self.s = set()
        for e in self.q:
            if e[0] >= t:
                new_q.append(e)
                self.s.add(e[1])
        self.q = new_q

    def items(self):
        for e in self.q:
            yield e[1]

    def __contains__(self, item):
        return item in self.s