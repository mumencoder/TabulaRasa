
import os, sys
import asyncio
import collections
import random, time
import string, re, hashlib, io, binascii
import json, blowfish, zlib

import kazoo

async def write_now(writer, data):
    writer.write( data )
    await writer.drain()

async def request_and_wait(writer, reader, data):
    await write_now(writer, data)
    response = await reader.read(-1)
    return response