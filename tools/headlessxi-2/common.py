
import os, sys
import asyncio, threading
import collections
import math, random
import time
import pathlib
import string, re, hashlib, io, binascii, base64
import json, blowfish, zlib
import traceback

import mysql.connector
import kazoo, kazoo.client
import kafka

import util
import config

class Object(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class SimpleObject(Object):
    def from_dict(self, d):
        for key, value in d.items():
            setattr(self, key, value)

    def to_dict(self):
        d = {}
        for attr in vars(self):
            d[attr] = getattr(self, attr)
        return d

def zkfut( zk_async ):
    loop = asyncio.get_event_loop()
    f = loop.create_future()
    def cb(zk_async):
        try:
            loop.call_soon_threadsafe( f.set_result, zk_async.get() )
        except Exception as e:
            loop.call_soon_threadsafe( f.set_exception, e )
    zk_async.rawlink(cb)
    return f

class Coder:
    class Int32(object):
        def encode(i):
            return util.pack_32(i)

        def decode(bs):
            return util.unpack_uint32(bs, 0)

    class Json(object):
        def encode(d):
            return json.dumps(d)

        def decode(bs):
            return json.loads(bs)

class SQLHelper(object):
    def insert(obj, meta):
        q = f"INSERT INTO {meta.table} VALUES ("
        q += ",".join( ['%s' for i in range(0, len(meta.attrs))] )
        q += ')'
        values = [ getattr(obj, attr) for attr in meta.attrs.keys() ]
        return (q, values)

    def read_row(obj, meta, row):
        for i, (attr, info) in enumerate(meta.attrs.items()):
            setattr(obj, attr, row[i])

class ZKHelper(object):
    def __init__(self, zk):
        self.zk = zk
        self.fields = {}
        self.get_meta = {}

    def declare(self, name, handler):
        self.zk.ensure_path(name)
        self.fields[name] = handler

    async def set_now(self, name, value, handler=None):
        if handler is None:
            handler = self.fields[name]
        return await zkfut( self.zk.set_async( name, handler.encode( value ) ) )

    async def get_now(self, name, handler=None):
        if handler is None:
            handler = self.fields[name]
        rval = await zkfut( self.zk.get_async("himi/current_account") )
        self.get_meta[name] = rval[1]
        return handler.decode( rval[0] )

