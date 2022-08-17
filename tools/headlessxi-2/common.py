
import os, sys
import asyncio
import collections
import math, random
import time
import string, re, hashlib, io, binascii
import json, blowfish, zlib
import traceback

import mysql.connector
import kazoo

async def write_now(writer, data):
    writer.write( data )
    await writer.drain()

async def request_and_wait(writer, reader, data):
    await write_now(writer, data)
    response = await reader.read(-1)
    return response

class Point(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_dict(d):
        return Point(d["x"], d["y"], d["z"])

    def __str__(self):
        return f"{self.x} {self.y} {self.z}"