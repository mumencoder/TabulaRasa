
import sys
import kafka
import json
import base64, binascii

import matplotlib.pyplot as pyplot

from packets import *
import util

args = {}
args = {"since":0, "character":"Smolcat", "id_lo":None, "id_hi":None}
#args = {"since":0, "character":"Noocat", "id_lo":None, "id_hi":None}
#args = {"since":0, "character":"XZolyooze", "id_lo":None, "id_hi":None}

packet_parsers = {}
packet_parsers['lobby-data-in'] = parse_lobby_data_c2s
packet_parsers['lobby-data-out'] = parse_lobby_data_s2c
packet_parsers['lobby-view-in'] = parse_lobby_view_c2s
packet_parsers['lobby-view-out'] = parse_lobby_view_s2c

def get_events(topics):
    parts = [kafka.TopicPartition(topic, 0) for topic in topics]
    consumer = kafka.KafkaConsumer(bootstrap_servers='172.31.177.56:9092')
    consumer.assign(parts)

    for part in parts:
        consumer.seek(part, 0)

    events = []
    while True:
        print(len(events))
        results = consumer.poll(timeout_ms=10000)
        if len(results) == 0:
            break
        for msgs in results.values():
            for msg in msgs:
                events.append( {"msg":msg, "value":json.loads(msg.value)})
    return events

def lobby_topics():
    topics = ['lobby-data-in', 'lobby-data-out', 'lobby-view-in', 'lobby-view-out', 'lobby-socket']
    events = get_events(topics)

    for event in sorted( events, key=lambda event: event["value"]["id"] ):
        event["value"]["data"] = base64.b64decode( event["value"]["data"])
        if len(event["value"]["data"]) == 0:
            continue 
        ppacket = packet_parsers[event["msg"].topic]( event["value"]["data"] )

def map_topics():
    xs = []
    zs = []
    topics = ['packets-in', 'packets-out']
    events = get_events(topics)

    for event in sorted( events, key=lambda event: event["value"]["id"] ):
        msg = event["msg"]
        value = event["value"]
        if "since" in args and float(value["timestamp"]) < float(args["since"]):
            continue
        if "character" in args and value["character"]["name"] != args["character"]:
            continue
        epacket = value["packet"]
        epacket["type"] = int( epacket["type"] )
        epacket["hextype"] = hex( epacket["type"] )
        if msg.topic == "packets-out":
            epacket["desc"] = MapPacket.s2c[ epacket["type"] ]["descs"]
        if msg.topic == "packets-in":
            epacket["desc"] = MapPacket.c2s[ epacket["type"] ]["descs"]

        if msg.topic == "packets-in" and epacket['hextype'] == '0x15':
            pass
        elif msg.topic == "packets-out" and epacket['hextype'] == '0xe':
            pass
        else:
            del epacket["data"]
            del epacket["type"]
            del value["session"]
            print(msg.topic, value)
        

#lobby_topics()    
map_topics()